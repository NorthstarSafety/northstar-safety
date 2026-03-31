from __future__ import annotations

import html
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone
import urllib.parse
import urllib.request
from typing import Any

from .config import settings
from .demo_data import ALERTS, CASE_OVERRIDES, SEED_SETTINGS, build_seed_products
from .domain import (
    CLASSIFICATION_LABELS,
    build_evidence_template,
    case_default_from_confidence,
    classify_product,
    compute_match,
    derive_evidence_status,
    make_id,
    now_iso,
    slugify,
)
from .repository import (
    consume_oauth_state,
    create_oauth_state,
    effective_shopify_config,
    get_setting,
    mark_shop_synced,
    record_billing_event,
    refresh_evidence_statuses,
    set_setting,
    upsert_shop_install,
)


REQUIREMENT_BY_DOC_TYPE = {
    "CPC": "cpc",
    "Lab Report": "lab_report",
    "Tracking Label": "tracking_label",
    "Registration Proof": "registration_card",
    "Manual": "instruction_manual",
    "Supplier Packet": "supplier_packet",
    "Age Grade": "age_grade",
    "Food Contact": "food_contact",
    "Battery Review": "battery_review",
    "Warning Art": "warning_art",
}


SHOPIFY_PRODUCTS_QUERY = """
query NorthstarCatalog($cursor: String) {
  shop {
    name
    primaryDomain {
      host
    }
  }
  products(first: 50, after: $cursor, sortKey: UPDATED_AT) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        handle
        vendor
        productType
        status
        tags
        createdAt
        updatedAt
        variants(first: 100) {
          edges {
            node {
              id
              title
              displayName
              sku
              barcode
              price
              inventoryQuantity
            }
          }
        }
      }
    }
  }
}
"""

SHOPIFY_INSTALL_STATUS_QUERY = """
query NorthstarInstallStatus {
  shop {
    name
    email
    primaryDomain {
      host
      url
    }
    plan {
      displayName
      partnerDevelopment
      shopifyPlus
    }
  }
  currentAppInstallation {
    id
    launchUrl
    accessScopes {
      handle
    }
    activeSubscriptions {
      id
      name
      status
      test
      currentPeriodEnd
      lineItems {
        plan {
          pricingDetails {
            __typename
            ... on AppRecurringPricing {
              interval
              price {
                amount
                currencyCode
              }
            }
          }
        }
      }
    }
  }
}
"""

SHOPIFY_SUBSCRIPTION_CREATE_MUTATION = """
mutation NorthstarSubscriptionCreate(
  $name: String!
  $lineItems: [AppSubscriptionLineItemInput!]!
  $returnUrl: URL!
  $trialDays: Int
  $test: Boolean
) {
  appSubscriptionCreate(
    name: $name
    returnUrl: $returnUrl
    lineItems: $lineItems
    trialDays: $trialDays
    test: $test
  ) {
    userErrors {
      field
      message
    }
    appSubscription {
      id
    }
    confirmationUrl
  }
}
"""

SHOP_DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$")


class ShopifySyncError(RuntimeError):
    """Raised when Shopify sync cannot complete."""


def ensure_seeded(connection) -> None:
    count = int(connection.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"])
    if count > 0:
        return

    config = effective_shopify_config(connection)
    if get_setting(connection, "catalog_mode", "") == "shopify" or (
        config["store_domain"] and (config["token_present"] or config["client_credentials_present"])
    ):
        set_setting(connection, "catalog_mode", "shopify")
        if config["store_domain"]:
            set_setting(connection, "shopify_store_domain", _normalise_shopify_domain(config["store_domain"]))
        if config["api_version"]:
            set_setting(connection, "shopify_api_version", config["api_version"])
        connection.commit()
        return

    seed_demo_workspace(connection)


def _clear_workspace(connection) -> None:
    for table in (
        "case_events",
        "cases",
        "matches",
        "evidence_items",
        "documents",
        "variants",
        "alerts",
        "products",
        "sync_runs",
        "settings",
    ):
        connection.execute(f"DELETE FROM {table}")
    connection.commit()


def _record_sync_run(
    connection,
    source_name: str,
    run_type: str,
    status: str,
    records_processed: int,
    records_created: int,
    records_updated: int,
    notes: str,
    started_at: str,
    completed_at: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO sync_runs (
            id, source_name, run_type, status, records_processed, records_created,
            records_updated, notes, started_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            make_id("sync"),
            source_name,
            run_type,
            status,
            records_processed,
            records_created,
            records_updated,
            notes,
            started_at,
            completed_at,
        ),
    )
    connection.commit()


def seed_demo_workspace(connection) -> dict[str, int]:
    started_at = now_iso()
    _clear_workspace(connection)

    for key, value in SEED_SETTINGS.items():
        set_setting(connection, key, value)
    set_setting(connection, "shopify_store_domain", settings.shopify_store_domain)
    set_setting(connection, "shopify_admin_token_present", "yes" if settings.shopify_admin_token else "no")
    set_setting(connection, "live_cpsc_enabled", "yes" if settings.enable_live_cpsc else "no")

    products = build_seed_products()
    created_documents = 0
    created_evidence = 0
    now = now_iso()

    for product in products:
        connection.execute(
            """
            INSERT INTO products (
                id, shopify_product_id, catalog_source, title, handle, vendor, product_type, status, classification,
                jurisdiction_scope, supplier_name, country_of_origin, age_grade, tags_json,
                created_at, updated_at, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["id"],
                product["shopify_product_id"],
                "demo",
                product["title"],
                product["handle"],
                product["vendor"],
                product["product_type"],
                product["status"],
                product["classification"],
                product["jurisdiction_scope"],
                product["supplier_name"],
                product["country_of_origin"],
                product["age_grade"],
                json.dumps(product["tags"]),
                now,
                now,
                now,
            ),
        )
        for variant in product["variants"]:
            connection.execute(
                """
                INSERT INTO variants (
                    id, product_id, shopify_variant_id, sku, title, barcode, price,
                    inventory_quantity, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    variant["id"],
                    product["id"],
                    variant["shopify_variant_id"],
                    variant["sku"],
                    variant["title"],
                    variant["barcode"],
                    variant["price"],
                    variant["inventory_quantity"],
                    variant["status"],
                    now,
                    now,
                ),
            )

        doc_links: dict[str, dict[str, Any]] = {}
        for document in product["documents"]:
            connection.execute(
                """
                INSERT INTO documents (
                    id, product_id, title, doc_type, issuer, source_url, file_name, stored_path, status,
                    issued_at, valid_until, verified_at, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document["id"],
                    product["id"],
                    document["title"],
                    document["doc_type"],
                    document["issuer"],
                    document["source_url"],
                    None,
                    None,
                    document["status"],
                    document["issued_at"],
                    document["valid_until"],
                    document["verified_at"],
                    document["notes"],
                    now,
                    now,
                ),
            )
            created_documents += 1
            requirement_code = REQUIREMENT_BY_DOC_TYPE.get(document["doc_type"])
            if requirement_code and requirement_code not in product["missing_requirements"]:
                doc_links[requirement_code] = document

        for requirement in product["evidence_template"]:
            document = doc_links.get(requirement["requirement_code"])
            linked_document_id = document["id"] if document else None
            stale_after = document["valid_until"] if document else None
            status = derive_evidence_status(document, stale_after)
            connection.execute(
                """
                INSERT INTO evidence_items (
                    id, product_id, requirement_code, title, description, status, last_checked_at,
                    stale_after, document_id, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("evi"),
                    product["id"],
                    requirement["requirement_code"],
                    requirement["title"],
                    requirement["description"],
                    status,
                    now,
                    stale_after,
                    linked_document_id,
                    "" if document else "Awaiting document or founder upload.",
                    now,
                    now,
                ),
            )
            created_evidence += 1

    for alert in ALERTS:
        connection.execute(
            """
            INSERT INTO alerts (
                id, source_name, source_id, title, alert_date, jurisdiction, product_name, hazard,
                description, source_url, severity, status, raw_payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert["id"],
                alert["source_name"],
                alert["source_id"],
                alert["title"],
                alert["alert_date"],
                alert["jurisdiction"],
                alert["product_name"],
                alert["hazard"],
                alert["description"],
                alert["source_url"],
                alert["severity"],
                alert["status"],
                json.dumps(alert, sort_keys=True),
                now,
                now,
            ),
        )

    connection.commit()
    recompute_matches_and_cases(connection)
    refresh_evidence_statuses(connection)
    _record_sync_run(
        connection,
        source_name="demo-seed",
        run_type="bootstrap",
        status="completed",
        records_processed=len(products) + len(ALERTS),
        records_created=len(products) + created_documents + created_evidence + len(ALERTS),
        records_updated=0,
        notes="Seeded realistic demo catalog, evidence, alerts, matches, and cases.",
        started_at=started_at,
        completed_at=now_iso(),
    )
    return {
        "products": len(products),
        "documents": created_documents,
        "evidence_items": created_evidence,
        "alerts": len(ALERTS),
    }


def recompute_matches_and_cases(connection) -> dict[str, int]:
    products = [
        {
            **dict(row),
            "tags": json.loads(row["tags_json"]),
        }
        for row in connection.execute("SELECT * FROM products").fetchall()
    ]
    alerts = [dict(row) for row in connection.execute("SELECT * FROM alerts").fetchall()]
    created_matches = 0
    created_cases = 0
    updated_cases = 0
    auto_closed_cases = 0
    valid_pairs: set[tuple[str, str]] = set()

    for alert in alerts:
        for product in products:
            result = compute_match(product, alert)
            if result["confidence"] == "none":
                continue
            valid_pairs.add((alert["id"], product["id"]))
            existing = connection.execute(
                "SELECT id, status, operator_note, reviewed_at, reviewed_by FROM matches WHERE alert_id = ? AND product_id = ?",
                (alert["id"], product["id"]),
            ).fetchone()
            now = now_iso()
            match_status = "candidate"
            if existing:
                match_status = existing["status"]
                connection.execute(
                    """
                    UPDATE matches
                    SET score = ?, confidence = ?, rationale = ?, status = ?, operator_note = ?, reviewed_at = ?, reviewed_by = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        result["score"],
                        result["confidence"],
                        result["rationale"],
                        existing["status"],
                        existing["operator_note"],
                        existing["reviewed_at"],
                        existing["reviewed_by"],
                        now,
                        existing["id"],
                    ),
                )
            else:
                variant = connection.execute(
                    "SELECT id FROM variants WHERE product_id = ? ORDER BY title LIMIT 1",
                    (product["id"],),
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO matches (
                        id, alert_id, product_id, variant_id, score, confidence, rationale, status,
                        operator_note, reviewed_at, reviewed_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        make_id("match"),
                        alert["id"],
                        product["id"],
                        variant["id"] if variant else None,
                        result["score"],
                        result["confidence"],
                        result["rationale"],
                        "candidate",
                        "",
                        None,
                        None,
                        now,
                        now,
                    ),
                )
                created_matches += 1

            if match_status == "dismissed":
                continue

            should_open_case = (
                match_status == "confirmed"
                or result["confidence"] == "high"
                or (alert["id"], product["id"]) in CASE_OVERRIDES
            )

            default_status, default_decision, default_priority = case_default_from_confidence(
                result["confidence"],
                alert["severity"],
            )
            override = CASE_OVERRIDES.get((alert["id"], product["id"]), {})
            owner_row = connection.execute(
                "SELECT value FROM settings WHERE key = 'default_owner'"
            ).fetchone()
            owner = override.get("owner") or (owner_row["value"] if owner_row else "Unassigned")
            triage_status = override.get("triage_status", default_status)
            decision = override.get("decision", default_decision)
            priority = override.get("priority", default_priority)
            summary = override.get("summary", f"{result['confidence'].title()} confidence alert-product match created.")
            existing_case = connection.execute(
                "SELECT id, triage_status FROM cases WHERE alert_id = ? AND product_id = ?",
                (alert["id"], product["id"]),
            ).fetchone()

            if not should_open_case:
                if existing_case and existing_case["triage_status"] != "closed":
                    connection.execute(
                        """
                        UPDATE cases
                        SET triage_status = 'closed',
                            decision = ?,
                            last_action_summary = ?,
                            closed_at = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            "Awaiting operator confirmation",
                            "Northstar auto-closed this case because the current match remains review-only until an operator confirms it.",
                            now,
                            now,
                            existing_case["id"],
                        ),
                    )
                    auto_closed_cases += 1
                    connection.execute(
                        """
                        INSERT INTO case_events (
                            id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            make_id("evt"),
                            existing_case["id"],
                            "case_auto_closed",
                            "Northstar sync",
                            "Match remains review-only after the latest sync. Confirm it before reopening a case.",
                            alert["source_url"],
                            json.dumps({"reason": "review_only"}, sort_keys=True),
                            now,
                        ),
                    )
                continue

            if existing_case:
                if existing_case["triage_status"] == "closed":
                    connection.execute(
                        """
                        UPDATE cases
                        SET triage_status = ?,
                            decision = ?,
                            priority = ?,
                            closed_at = NULL,
                            last_action_summary = ?,
                            source_link = ?,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            triage_status,
                            decision,
                            priority,
                            summary,
                            alert["source_url"],
                            now,
                            existing_case["id"],
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO case_events (
                            id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            make_id("evt"),
                            existing_case["id"],
                            "case_reopened",
                            "Northstar sync",
                            "A current sync restored a high-confidence overlap, so Northstar reopened this case.",
                            alert["source_url"],
                            json.dumps({"reason": "high_confidence_sync"}, sort_keys=True),
                            now,
                        ),
                    )
                else:
                    connection.execute(
                        """
                        UPDATE cases
                        SET source_link = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (alert["source_url"], now, existing_case["id"]),
                    )
                updated_cases += 1
                case_id = existing_case["id"]
            else:
                case_id = make_id("case")
                connection.execute(
                    """
                    INSERT INTO cases (
                        id, alert_id, product_id, owner, triage_status, decision, priority,
                        opened_at, updated_at, closed_at, last_action_summary, source_link
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_id,
                        alert["id"],
                        product["id"],
                        owner,
                        triage_status,
                        decision,
                        priority,
                        now,
                        now,
                        now if triage_status == "closed" else None,
                        summary,
                        alert["source_url"],
                    ),
                )
                created_cases += 1

            event_count = int(
                connection.execute(
                    "SELECT COUNT(*) AS count FROM case_events WHERE case_id = ?",
                    (case_id,),
                ).fetchone()["count"]
            )
            if event_count == 0:
                for event in override.get("events", []):
                    connection.execute(
                        """
                        INSERT INTO case_events (
                            id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            make_id("evt"),
                            case_id,
                            event["event_type"],
                            event["actor_name"],
                            event["note"],
                            event.get("source_url") or None,
                            json.dumps({"seeded": True}, sort_keys=True),
                            now,
                        ),
                    )

    now = now_iso()
    stale_matches = connection.execute(
        """
        SELECT m.id, m.alert_id, m.product_id, m.status, m.operator_note, c.id AS case_id, c.triage_status
        FROM matches m
        LEFT JOIN cases c ON c.alert_id = m.alert_id AND c.product_id = m.product_id
        """
    ).fetchall()
    for row in stale_matches:
        pair = (row["alert_id"], row["product_id"])
        if pair in valid_pairs or row["status"] == "confirmed":
            continue
        if row["status"] != "dismissed":
            operator_note = row["operator_note"] or "Auto-cleared after catalog refresh removed the practical overlap."
            connection.execute(
                """
                UPDATE matches
                SET status = 'dismissed', operator_note = ?, reviewed_at = ?, reviewed_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (operator_note, now, "Northstar sync", now, row["id"]),
            )
        if row["case_id"] and row["triage_status"] != "closed":
            connection.execute(
                """
                UPDATE cases
                SET triage_status = 'closed',
                    decision = ?,
                    last_action_summary = ?,
                    closed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    "No current overlap after catalog refresh",
                    "Northstar auto-closed this case after the latest catalog refresh removed the match overlap.",
                    now,
                    now,
                    row["case_id"],
                ),
            )
            auto_closed_cases += 1
            connection.execute(
                """
                INSERT INTO case_events (id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("evt"),
                    row["case_id"],
                    "match_auto_closed",
                    "Northstar sync",
                    "Catalog refresh removed the practical overlap, so the case was auto-closed.",
                    None,
                    json.dumps({"match_id": row["id"]}, sort_keys=True),
                    now,
                ),
            )

    connection.commit()
    return {
        "matches": created_matches,
        "cases_created": created_cases,
        "cases_updated": updated_cases,
        "cases_auto_closed": auto_closed_cases,
    }


def sync_demo_catalog(connection) -> dict[str, Any]:
    started_at = now_iso()
    products = connection.execute("SELECT id FROM products").fetchall()
    if not products:
        seeded = seed_demo_workspace(connection)
        return {
            "status": "completed",
            "records_processed": seeded["products"],
            "records_created": seeded["products"],
            "records_updated": 0,
            "notes": "Seeded demo catalog because the workspace was empty.",
        }

    now = now_iso()
    updated = connection.execute(
        "UPDATE products SET last_synced_at = ?, updated_at = ?",
        (now, now),
    ).rowcount
    connection.commit()
    _record_sync_run(
        connection,
        source_name="shopify-demo",
        run_type="catalog-sync",
        status="completed",
        records_processed=updated,
        records_created=0,
        records_updated=updated,
        notes="Demo catalog refreshed from local fixture set.",
        started_at=started_at,
        completed_at=now_iso(),
    )
    return {
        "status": "completed",
        "records_processed": updated,
        "records_created": 0,
        "records_updated": updated,
        "notes": "Demo catalog refresh complete.",
    }


def _normalise_shopify_domain(store_domain: str) -> str:
    cleaned = store_domain.strip().replace("https://", "").replace("http://", "")
    cleaned = cleaned.split("/")[0].strip()
    if not cleaned:
        return ""
    if cleaned.startswith("localhost") or cleaned.startswith("127.0.0.1"):
        return cleaned
    if not cleaned.endswith(".myshopify.com"):
        cleaned = f"{cleaned}.myshopify.com"
    return cleaned


def _shopify_internal_id(prefix: str, gid: str, fallback: str) -> str:
    tail = gid.rsplit("/", 1)[-1]
    tail = tail if tail.isdigit() else slugify(fallback)
    return f"{prefix}-{tail}"


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _token_is_fresh(expires_at: str) -> bool:
    expiry = _parse_iso_datetime(expires_at)
    if not expiry:
        return False
    return expiry > datetime.now(timezone.utc) + timedelta(minutes=2)


def _shopify_api_base(store_domain: str, api_version: str) -> str:
    scheme = "http" if store_domain.startswith("localhost") or store_domain.startswith("127.0.0.1") else "https"
    return f"{scheme}://{store_domain}/admin/api/{api_version}"


def _shopify_graphql_request(
    *,
    store_domain: str,
    access_token: str,
    api_version: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    endpoint = f"{_shopify_api_base(store_domain, api_version)}/graphql.json"
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
            "User-Agent": "NorthstarSafetyPrototype/0.4",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ShopifySyncError(f"Shopify request failed with HTTP {exc.code}: {detail[:400]}") from exc
    if body.get("errors"):
        raise ShopifySyncError(f"Shopify returned GraphQL errors: {body['errors']}")
    return body["data"]


def _valid_shop_domain(shop_domain: str) -> bool:
    return bool(SHOP_DOMAIN_PATTERN.match(shop_domain))


def _clean_next_path(next_path: str) -> str:
    if next_path and next_path.startswith("/"):
        return next_path
    return settings.shopify_install_redirect_path


def _verify_shopify_oauth_hmac(params: dict[str, str], client_secret: str) -> bool:
    if not client_secret:
        return False
    provided_hmac = params.get("hmac", "")
    if not provided_hmac:
        return False
    message = "&".join(
        f"{key}={value}"
        for key, value in sorted(
            (key, value)
            for key, value in params.items()
            if key not in {"hmac", "signature"}
        )
    )
    digest = hmac.new(client_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided_hmac)


def _exchange_shopify_access_token(connection) -> str:
    config = effective_shopify_config(connection)
    store_domain = _normalise_shopify_domain(config["store_domain"])
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    if not store_domain or not client_id or not client_secret:
        raise ShopifySyncError("Shopify store domain, client ID, and client secret are required to exchange a live access token.")

    payload = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://{store_domain}/admin/oauth/access_token",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "NorthstarSafetyPrototype/0.3",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ShopifySyncError(f"Shopify token exchange failed with HTTP {exc.code}: {detail[:400]}") from exc

    token = body.get("access_token", "").strip()
    if not token:
        raise ShopifySyncError("Shopify token exchange succeeded but did not return an access token.")

    expires_in = int(body.get("expires_in") or 0)
    expires_at = ""
    if expires_in > 0:
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat().replace("+00:00", "Z")
        set_setting(connection, "shopify_admin_token_expires_at", expires_at)
    set_setting(connection, "shopify_admin_token", token)
    set_setting(connection, "shopify_admin_token_present", "yes")
    if body.get("scope"):
        set_setting(connection, "shopify_admin_token_scope", str(body["scope"]))
    connection.commit()
    return token


def _resolve_shopify_access_token(connection) -> str:
    config = effective_shopify_config(connection)
    if config["token_present"]:
        if not config["token_expires_at"] or _token_is_fresh(config["token_expires_at"]):
            return config["token"]
    if config["client_credentials_present"]:
        return _exchange_shopify_access_token(connection)
    raise ShopifySyncError("Add a Shopify admin token or client credentials before running live sync.")


def _shopify_graphql(connection, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    config = effective_shopify_config(connection)
    store_domain = _normalise_shopify_domain(config["store_domain"])
    token = _resolve_shopify_access_token(connection)
    api_version = config["api_version"] or settings.shopify_api_version
    if not store_domain or not token:
        raise ShopifySyncError("Shopify store domain and credentials are required for live sync.")
    return _shopify_graphql_request(
        store_domain=store_domain,
        access_token=token,
        api_version=api_version,
        query=query,
        variables=variables,
    )


def create_shopify_install_url(connection, *, shop_domain: str, next_path: str = "", public_base_url: str = "") -> str:
    config = effective_shopify_config(connection)
    client_id = config["client_id"]
    if not client_id:
        raise ShopifySyncError("Shopify client ID is required before Northstar can start an install.")

    store_domain = _normalise_shopify_domain(shop_domain)
    if not _valid_shop_domain(store_domain):
        raise ShopifySyncError("Enter a valid Shopify domain such as store-name.myshopify.com.")

    state_expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
    state = create_oauth_state(
        connection,
        shop_domain=store_domain,
        next_path=_clean_next_path(next_path),
        expires_at=state_expires_at,
    )
    redirect_uri = f"{(public_base_url or settings.public_base_url).rstrip('/')}/auth/callback"
    params = {
        "client_id": client_id,
        "scope": settings.shopify_app_scopes,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    query = urllib.parse.urlencode(params)
    return f"https://{store_domain}/admin/oauth/authorize?{query}"


def _exchange_oauth_code_for_access_token(*, shop_domain: str, client_id: str, client_secret: str, code: str) -> dict[str, Any]:
    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://{shop_domain}/admin/oauth/access_token",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "NorthstarSafetyPrototype/0.4",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ShopifySyncError(f"Shopify OAuth token exchange failed with HTTP {exc.code}: {detail[:400]}") from exc


def complete_shopify_install(connection, *, params: dict[str, str]) -> dict[str, Any]:
    config = effective_shopify_config(connection)
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    if not client_id or not client_secret:
        raise ShopifySyncError("Shopify client ID and client secret are required before Northstar can complete an install.")

    shop_domain = _normalise_shopify_domain(params.get("shop", ""))
    state = params.get("state", "")
    code = params.get("code", "")
    if not _valid_shop_domain(shop_domain):
        raise ShopifySyncError("Shopify returned an invalid shop domain during install.")
    if not state or not code:
        raise ShopifySyncError("Shopify did not return the full OAuth callback payload.")
    if not _verify_shopify_oauth_hmac(params, client_secret):
        raise ShopifySyncError("Shopify OAuth callback HMAC verification failed.")

    pending_state = consume_oauth_state(connection, state)
    if not pending_state:
        raise ShopifySyncError("The Shopify install session is missing or expired. Start the install again.")
    if pending_state["shop_domain"] != shop_domain:
        raise ShopifySyncError("The Shopify install callback shop did not match the original request.")
    state_expiry = _parse_iso_datetime(pending_state["expires_at"])
    if not state_expiry or state_expiry <= datetime.now(timezone.utc):
        raise ShopifySyncError("The Shopify install session expired before the callback completed. Start again.")

    token_body = _exchange_oauth_code_for_access_token(
        shop_domain=shop_domain,
        client_id=client_id,
        client_secret=client_secret,
        code=code,
    )
    access_token = str(token_body.get("access_token", "")).strip()
    scope = str(token_body.get("scope", "")).strip()
    if not access_token:
        raise ShopifySyncError("Shopify OAuth finished, but Northstar did not receive an access token.")

    install_data = _shopify_graphql_request(
        store_domain=shop_domain,
        access_token=access_token,
        api_version=config["api_version"] or settings.shopify_api_version,
        query=SHOPIFY_INSTALL_STATUS_QUERY,
    )
    shop = install_data.get("shop") or {}
    app_installation = install_data.get("currentAppInstallation") or {}
    upsert_shop_install(
        connection,
        shop_domain=shop_domain,
        access_token=access_token,
        scope=scope,
        app_installation_id=app_installation.get("id", ""),
        launch_url=app_installation.get("launchUrl", ""),
        shop_name=shop.get("name", ""),
        shop_email=shop.get("email", ""),
        primary_domain_host=((shop.get("primaryDomain") or {}).get("host") or ""),
        plan_name=((shop.get("plan") or {}).get("displayName") or ""),
        is_partner_development=bool((shop.get("plan") or {}).get("partnerDevelopment")),
        is_shopify_plus=bool((shop.get("plan") or {}).get("shopifyPlus")),
    )

    set_setting(connection, "catalog_mode", "shopify")
    set_setting(connection, "shopify_store_domain", shop_domain)
    set_setting(connection, "shopify_admin_token", access_token)
    set_setting(connection, "shopify_admin_token_present", "yes")
    set_setting(connection, "shopify_admin_token_expires_at", "")
    set_setting(connection, "shopify_admin_token_scope", scope or settings.shopify_app_scopes)
    set_setting(connection, "shopify_client_id", client_id)
    set_setting(connection, "shopify_client_secret", client_secret)
    set_setting(connection, "shopify_last_live_status", "connected")
    if get_setting(connection, "merchant_name", "") in {"", "Northstar Kids Co.", "My Store"} and shop.get("name"):
        set_setting(connection, "merchant_name", shop["name"])
    connection.commit()

    sync_result = None
    sync_warning = ""
    try:
        sync_result = sync_shopify_catalog(connection)
        mark_shop_synced(connection, shop_domain=shop_domain)
    except ShopifySyncError as exc:
        sync_warning = str(exc)

    return {
        "shop_domain": shop_domain,
        "shop_name": shop.get("name", shop_domain),
        "scope": scope or settings.shopify_app_scopes,
        "next_path": pending_state["next_path"],
        "sync_result": sync_result,
        "sync_warning": sync_warning,
        "install_status": install_data,
    }


def billing_snapshot(connection) -> dict[str, Any]:
    config = effective_shopify_config(connection)
    store_domain = _normalise_shopify_domain(config["store_domain"])
    token = _resolve_shopify_access_token(connection)
    if not store_domain or not token:
        raise ShopifySyncError("Connect a Shopify store before checking Northstar billing.")
    data = _shopify_graphql_request(
        store_domain=store_domain,
        access_token=token,
        api_version=config["api_version"] or settings.shopify_api_version,
        query=SHOPIFY_INSTALL_STATUS_QUERY,
    )
    current = data.get("currentAppInstallation") or {}
    subscriptions = current.get("activeSubscriptions") or []
    active = subscriptions[0] if subscriptions else None
    shop = data.get("shop") or {}
    upsert_shop_install(
        connection,
        shop_domain=store_domain,
        access_token=token,
        scope=",".join(scope.get("handle", "") for scope in current.get("accessScopes") or [] if scope.get("handle")),
        app_installation_id=current.get("id", ""),
        launch_url=current.get("launchUrl", ""),
        shop_name=shop.get("name", ""),
        shop_email=shop.get("email", ""),
        primary_domain_host=((shop.get("primaryDomain") or {}).get("host") or ""),
        plan_name=((shop.get("plan") or {}).get("displayName") or ""),
        is_partner_development=bool((shop.get("plan") or {}).get("partnerDevelopment")),
        is_shopify_plus=bool((shop.get("plan") or {}).get("shopifyPlus")),
    )
    return {
        "shop_domain": store_domain,
        "shop": shop,
        "app_installation": current,
        "active_subscription": active,
        "has_active_subscription": bool(active),
        "billing_required": settings.shopify_billing_required,
        "billing_plan_name": settings.shopify_billing_plan_name,
        "billing_price_usd": settings.shopify_billing_price_usd,
        "billing_trial_days": settings.shopify_billing_trial_days,
        "billing_test_mode": settings.shopify_billing_test_mode,
    }


def create_billing_subscription(connection, *, public_base_url: str = "") -> dict[str, Any]:
    snapshot = billing_snapshot(connection)
    if snapshot["has_active_subscription"]:
        return {
            "status": "active",
            "confirmation_url": "",
            "subscription": snapshot["active_subscription"],
            "notes": "Northstar already has an active Shopify subscription for this store.",
        }

    config = effective_shopify_config(connection)
    store_domain = _normalise_shopify_domain(config["store_domain"])
    token = _resolve_shopify_access_token(connection)
    variables = {
        "name": settings.shopify_billing_plan_name,
        "returnUrl": f"{(public_base_url or settings.public_base_url).rstrip('/')}{settings.shopify_billing_return_path}",
        "trialDays": settings.shopify_billing_trial_days or None,
        "test": settings.shopify_billing_test_mode,
        "lineItems": [
            {
                "plan": {
                    "appRecurringPricingDetails": {
                        "price": {"amount": settings.shopify_billing_price_usd, "currencyCode": "USD"},
                        "interval": settings.shopify_billing_interval,
                    }
                }
            }
        ],
    }
    data = _shopify_graphql_request(
        store_domain=store_domain,
        access_token=token,
        api_version=config["api_version"] or settings.shopify_api_version,
        query=SHOPIFY_SUBSCRIPTION_CREATE_MUTATION,
        variables=variables,
    )
    response = data["appSubscriptionCreate"]
    user_errors = response.get("userErrors") or []
    if user_errors:
        message = "; ".join(error.get("message", "Unknown billing error") for error in user_errors)
        if "currently owned by a Shop" in message:
            message = (
                "This Shopify app is still shop-owned. Move it into the Shopify Partners area before Northstar can use the Billing API."
            )
        record_billing_event(
            connection,
            shop_domain=store_domain,
            plan_name=settings.shopify_billing_plan_name,
            status="blocked",
            test_mode=settings.shopify_billing_test_mode,
            notes=message,
        )
        raise ShopifySyncError(message)

    confirmation_url = response.get("confirmationUrl", "")
    subscription = response.get("appSubscription") or {}
    notes = "Shopify returned a subscription confirmation URL."
    record_billing_event(
        connection,
        shop_domain=store_domain,
        plan_name=settings.shopify_billing_plan_name,
        status="pending",
        confirmation_url=confirmation_url,
        subscription_gid=subscription.get("id", ""),
        test_mode=settings.shopify_billing_test_mode,
        notes=notes,
    )
    return {
        "status": "pending",
        "confirmation_url": confirmation_url,
        "subscription": subscription,
        "notes": notes,
    }


def _reconcile_evidence_for_product(connection, product_id: str, classification: str, checked_at: str) -> None:
    template = build_evidence_template(classification)
    existing_items = {
        row["requirement_code"]: dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_items WHERE product_id = ?",
            (product_id,),
        ).fetchall()
    }
    for requirement in template:
        current = existing_items.get(requirement["requirement_code"])
        if current:
            connection.execute(
                """
                UPDATE evidence_items
                SET title = ?, description = ?, last_checked_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    requirement["title"],
                    requirement["description"],
                    checked_at,
                    checked_at,
                    current["id"],
                ),
            )
            continue
        connection.execute(
            """
            INSERT INTO evidence_items (
                id, product_id, requirement_code, title, description, status, last_checked_at,
                stale_after, document_id, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                make_id("evi"),
                product_id,
                requirement["requirement_code"],
                requirement["title"],
                requirement["description"],
                "missing",
                checked_at,
                None,
                None,
                "Created from current product classification during catalog sync.",
                checked_at,
                checked_at,
            ),
        )


def _delete_demo_catalog(connection) -> None:
    connection.execute("DELETE FROM products WHERE catalog_source = 'demo'")
    connection.commit()


def sync_shopify_catalog(connection) -> dict[str, Any]:
    started_at = now_iso()
    config = effective_shopify_config(connection)
    store_domain = _normalise_shopify_domain(config["store_domain"])
    api_version = config["api_version"] or settings.shopify_api_version
    if not store_domain or (not config["token_present"] and not config["client_credentials_present"]):
        _record_sync_run(
            connection,
            source_name="shopify-live",
            run_type="catalog-sync",
            status="failed",
            records_processed=0,
            records_created=0,
            records_updated=0,
            notes="Missing Shopify store domain or live credentials.",
            started_at=started_at,
            completed_at=now_iso(),
        )
        raise ShopifySyncError("Add a Shopify store domain plus either an admin token or client credentials before running live sync.")

    existing_shopify_count = int(
        connection.execute("SELECT COUNT(*) AS count FROM products WHERE catalog_source = 'shopify'").fetchone()["count"]
    )
    demo_count = int(
        connection.execute("SELECT COUNT(*) AS count FROM products WHERE catalog_source = 'demo'").fetchone()["count"]
    )

    cursor = None
    products_payload: list[dict[str, Any]] = []
    shop_name = ""
    while True:
        response = _shopify_graphql(connection, SHOPIFY_PRODUCTS_QUERY, {"cursor": cursor})
        shop = response.get("shop") or {}
        shop_name = shop_name or shop.get("name", "")
        edges = response["products"]["edges"]
        for edge in edges:
            products_payload.append(edge["node"])
        page_info = response["products"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    if not products_payload:
        if existing_shopify_count == 0 and demo_count > 0:
            _delete_demo_catalog(connection)
            recompute_matches_and_cases(connection)
        elif existing_shopify_count > 0:
            now = now_iso()
            connection.execute(
                "UPDATE products SET status = 'archived', updated_at = ?, last_synced_at = ? WHERE catalog_source = 'shopify'",
                (now, now),
            )
        if get_setting(connection, "merchant_name", "") in {"", "Northstar Kids Co."} and shop_name:
            set_setting(connection, "merchant_name", shop_name)
        set_setting(connection, "catalog_mode", "shopify")
        set_setting(connection, "shopify_store_domain", store_domain)
        set_setting(connection, "shopify_api_version", api_version)
        set_setting(connection, "shopify_last_product_count", "0")
        set_setting(connection, "shopify_last_live_status", "empty")
        connection.commit()
        mark_shop_synced(connection, shop_domain=store_domain)
        _record_sync_run(
            connection,
            source_name="shopify-live",
            run_type="catalog-sync",
            status="completed",
            records_processed=0,
            records_created=0,
            records_updated=0,
            notes=f"Connected to {store_domain} but found zero products. Live workspace has been left empty until products exist in Shopify.",
            started_at=started_at,
            completed_at=now_iso(),
        )
        return {
            "status": "completed",
            "records_processed": 0,
            "records_created": 0,
            "records_updated": 0,
            "notes": f"Connected to {store_domain}, but the store returned zero products.",
        }

    existing_shopify_rows = {
        row["shopify_product_id"]: dict(row)
        for row in connection.execute(
            """
            SELECT id, shopify_product_id, supplier_name, country_of_origin, age_grade, jurisdiction_scope, classification
            FROM products
            WHERE shopify_product_id IS NOT NULL AND catalog_source = 'shopify'
            """
        ).fetchall()
    }
    if existing_shopify_count == 0 and demo_count > 0:
        _delete_demo_catalog(connection)

    jurisdiction_scope = get_setting(connection, "jurisdictions", "United States, Canada")
    created = 0
    updated = 0
    variant_count = 0
    now = now_iso()
    live_product_ids: set[str] = set()

    for node in products_payload:
        shopify_product_id = node["id"]
        live_product_ids.add(shopify_product_id)
        existing = existing_shopify_rows.get(shopify_product_id)
        product_id = existing["id"] if existing else _shopify_internal_id("shopify-product", shopify_product_id, node["handle"] or node["title"])
        tags = node.get("tags") or []
        classification = existing["classification"] if existing and existing.get("classification") else classify_product(node.get("title", ""), node.get("productType", ""), tags)
        payload = {
            "id": product_id,
            "shopify_product_id": shopify_product_id,
            "catalog_source": "shopify",
            "title": node.get("title") or "Untitled product",
            "handle": node.get("handle") or slugify(node.get("title") or "product"),
            "vendor": node.get("vendor") or shop_name or store_domain,
            "product_type": node.get("productType") or "Uncategorized",
            "status": (node.get("status") or "ACTIVE").lower(),
            "classification": classification,
            "jurisdiction_scope": existing["jurisdiction_scope"] if existing and existing["jurisdiction_scope"] else jurisdiction_scope,
            "supplier_name": existing["supplier_name"] if existing else "",
            "country_of_origin": existing["country_of_origin"] if existing else "",
            "age_grade": existing["age_grade"] if existing else "",
            "tags_json": json.dumps(tags),
            "created_at": node.get("createdAt") or now,
            "updated_at": node.get("updatedAt") or now,
            "last_synced_at": now,
        }

        if existing:
            connection.execute(
                """
                UPDATE products
                SET catalog_source = :catalog_source,
                    title = :title,
                    handle = :handle,
                    vendor = :vendor,
                    product_type = :product_type,
                    status = :status,
                    classification = :classification,
                    jurisdiction_scope = :jurisdiction_scope,
                    supplier_name = :supplier_name,
                    country_of_origin = :country_of_origin,
                    age_grade = :age_grade,
                    tags_json = :tags_json,
                    updated_at = :updated_at,
                    last_synced_at = :last_synced_at
                WHERE id = :id
                """,
                payload,
            )
            updated += 1
        else:
            connection.execute(
                """
                INSERT INTO products (
                    id, shopify_product_id, catalog_source, title, handle, vendor, product_type, status, classification,
                    jurisdiction_scope, supplier_name, country_of_origin, age_grade, tags_json,
                    created_at, updated_at, last_synced_at
                ) VALUES (
                    :id, :shopify_product_id, :catalog_source, :title, :handle, :vendor, :product_type, :status, :classification,
                    :jurisdiction_scope, :supplier_name, :country_of_origin, :age_grade, :tags_json,
                    :created_at, :updated_at, :last_synced_at
                )
                """,
                payload,
            )
            created += 1

        connection.execute("DELETE FROM variants WHERE product_id = ?", (product_id,))
        for edge in node.get("variants", {}).get("edges", []):
            variant = edge["node"]
            connection.execute(
                """
                INSERT INTO variants (
                    id, product_id, shopify_variant_id, sku, title, barcode, price,
                    inventory_quantity, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _shopify_internal_id("shopify-variant", variant["id"], variant.get("displayName") or variant.get("title") or "variant"),
                    product_id,
                    variant["id"],
                    variant.get("sku") or "",
                    variant.get("displayName") or variant.get("title") or "Default",
                    variant.get("barcode") or "",
                    float(variant.get("price") or 0),
                    int(variant.get("inventoryQuantity") or 0),
                    "active",
                    now,
                    now,
                ),
            )
            variant_count += 1

        _reconcile_evidence_for_product(connection, product_id, classification, now)

    stale_rows = connection.execute(
        """
        SELECT id FROM products
        WHERE catalog_source = 'shopify' AND shopify_product_id IS NOT NULL AND shopify_product_id NOT IN ({})
        """.format(",".join("?" for _ in live_product_ids)) if live_product_ids else """
        SELECT id FROM products WHERE 1 = 0
        """,
        tuple(live_product_ids),
    ).fetchall()
    for row in stale_rows:
        connection.execute(
            "UPDATE products SET status = 'archived', updated_at = ?, last_synced_at = ? WHERE id = ?",
            (now, now, row["id"]),
        )

    if get_setting(connection, "merchant_name", "") in {"", "Northstar Kids Co."} and shop_name:
        set_setting(connection, "merchant_name", shop_name)
    set_setting(connection, "catalog_mode", "shopify")
    set_setting(connection, "shopify_store_domain", store_domain)
    set_setting(connection, "shopify_api_version", api_version)
    set_setting(connection, "shopify_last_product_count", str(len(products_payload)))
    set_setting(connection, "shopify_last_live_status", "connected")
    set_setting(connection, "shopify_admin_token_present", "yes")

    refresh_evidence_statuses(connection)
    recompute_matches_and_cases(connection)
    connection.commit()
    mark_shop_synced(connection, shop_domain=store_domain)
    _record_sync_run(
        connection,
        source_name="shopify-live",
        run_type="catalog-sync",
        status="completed",
        records_processed=len(products_payload),
        records_created=created,
        records_updated=updated,
        notes=f"Synced {len(products_payload)} products and {variant_count} variants from {shop_name or store_domain}.",
        started_at=started_at,
        completed_at=now_iso(),
    )
    return {
        "status": "completed",
        "records_processed": len(products_payload),
        "records_created": created,
        "records_updated": updated,
        "notes": f"Synced {len(products_payload)} products from {shop_name or store_domain}.",
    }


def update_product_profile(
    connection,
    product_id: str,
    classification: str,
    supplier_name: str,
    country_of_origin: str,
    age_grade: str,
    jurisdiction_scope: str,
) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise ShopifySyncError("Product not found.")

    product = dict(row)
    selected_classification = classification if classification in CLASSIFICATION_LABELS else product["classification"]
    now = now_iso()
    connection.execute(
        """
        UPDATE products
        SET classification = ?, supplier_name = ?, country_of_origin = ?, age_grade = ?, jurisdiction_scope = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            selected_classification,
            supplier_name.strip(),
            country_of_origin.strip(),
            age_grade.strip(),
            jurisdiction_scope.strip() or product["jurisdiction_scope"] or "United States, Canada",
            now,
            product_id,
        ),
    )
    _reconcile_evidence_for_product(connection, product_id, selected_classification, now)
    refresh_evidence_statuses(connection)
    recompute_matches_and_cases(connection)
    connection.commit()
    return {"product_id": product_id, "classification": selected_classification}


def review_match(connection, match_id: str, review_status: str, reviewed_by: str, operator_note: str) -> dict[str, Any]:
    review_status = review_status.strip().lower()
    if review_status not in {"confirmed", "dismissed"}:
        raise ShopifySyncError("Match review status must be confirmed or dismissed.")
    if review_status == "dismissed" and not operator_note.strip():
        raise ShopifySyncError("Add a short reason before dismissing a match.")

    row = connection.execute(
        """
        SELECT m.*, a.id AS alert_id, a.title AS alert_title, a.severity, a.source_url,
               p.id AS product_id, p.title AS product_title, c.id AS case_id, c.triage_status
        FROM matches m
        JOIN alerts a ON a.id = m.alert_id
        JOIN products p ON p.id = m.product_id
        LEFT JOIN cases c ON c.alert_id = m.alert_id AND c.product_id = m.product_id
        WHERE m.id = ?
        """,
        (match_id,),
    ).fetchone()
    if not row:
        raise ShopifySyncError("Match not found.")

    match = dict(row)
    now = now_iso()
    connection.execute(
        """
        UPDATE matches
        SET status = ?, operator_note = ?, reviewed_at = ?, reviewed_by = ?, updated_at = ?
        WHERE id = ?
        """,
        (review_status, operator_note.strip(), now, reviewed_by.strip() or "Operator", now, match_id),
    )

    owner = get_setting(connection, "default_owner", "Unassigned")
    summary_note = operator_note.strip() or f"Match marked as {review_status} by operator."
    case_id = match.get("case_id")

    if review_status == "dismissed":
        if case_id:
            connection.execute(
                """
                UPDATE cases
                SET triage_status = 'closed',
                    decision = ?,
                    last_action_summary = ?,
                    closed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                ("Dismissed as false positive", summary_note, now, now, case_id),
            )
            connection.execute(
                """
                INSERT INTO case_events (id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("evt"),
                    case_id,
                    "match_dismissed",
                    reviewed_by.strip() or "Operator",
                    summary_note,
                    match["source_url"],
                    json.dumps({"match_id": match_id, "review_status": review_status}, sort_keys=True),
                    now,
                ),
            )
        connection.commit()
        return {"match_id": match_id, "status": review_status, "case_id": case_id}

    if review_status == "confirmed":
        if case_id:
            if match.get("triage_status") == "closed":
                connection.execute(
                    """
                    UPDATE cases
                    SET triage_status = 'under_review',
                        closed_at = NULL,
                        last_action_summary = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (summary_note, now, case_id),
                )
            connection.execute(
                """
                INSERT INTO case_events (id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("evt"),
                    case_id,
                    "match_confirmed",
                    reviewed_by.strip() or "Operator",
                    summary_note,
                    match["source_url"],
                    json.dumps({"match_id": match_id, "review_status": review_status}, sort_keys=True),
                    now,
                ),
            )
        else:
            default_status, default_decision, default_priority = case_default_from_confidence(match["confidence"], match["severity"])
            if default_status == "monitoring":
                default_status = "under_review"
            case_id = make_id("case")
            connection.execute(
                """
                INSERT INTO cases (
                    id, alert_id, product_id, owner, triage_status, decision, priority,
                    opened_at, updated_at, closed_at, last_action_summary, source_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    match["alert_id"],
                    match["product_id"],
                    owner,
                    default_status,
                    default_decision,
                    default_priority,
                    now,
                    now,
                    None,
                    summary_note,
                    match["source_url"],
                ),
            )
            connection.execute(
                """
                INSERT INTO case_events (id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("evt"),
                    case_id,
                    "match_confirmed",
                    reviewed_by.strip() or "Operator",
                    summary_note,
                    match["source_url"],
                    json.dumps({"match_id": match_id, "review_status": review_status}, sort_keys=True),
                    now,
                ),
            )

    connection.commit()
    return {"match_id": match_id, "status": review_status, "case_id": case_id}


def upsert_alert(connection, alert: dict[str, Any]) -> str:
    existing = connection.execute(
        "SELECT id FROM alerts WHERE source_id = ?",
        (alert["source_id"],),
    ).fetchone()
    now = now_iso()
    raw_payload = json.dumps(alert.get("raw_payload", alert), sort_keys=True)
    if existing:
        connection.execute(
            """
            UPDATE alerts
            SET title = ?, alert_date = ?, jurisdiction = ?, product_name = ?, hazard = ?, description = ?,
                source_url = ?, severity = ?, status = ?, raw_payload = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                alert["title"],
                alert["alert_date"],
                alert["jurisdiction"],
                alert["product_name"],
                alert["hazard"],
                alert["description"],
                alert["source_url"],
                alert["severity"],
                alert["status"],
                raw_payload,
                now,
                existing["id"],
            ),
        )
        connection.commit()
        return "updated"

    connection.execute(
        """
        INSERT INTO alerts (
            id, source_name, source_id, title, alert_date, jurisdiction, product_name, hazard,
            description, source_url, severity, status, raw_payload, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            make_id("alert"),
            alert["source_name"],
            alert["source_id"],
            alert["title"],
            alert["alert_date"],
            alert["jurisdiction"],
            alert["product_name"],
            alert["hazard"],
            alert["description"],
            alert["source_url"],
            alert["severity"],
            alert["status"],
            raw_payload,
            now,
            now,
        ),
    )
    connection.commit()
    return "created"


def _severity_from_text(*parts: str) -> str:
    text = " ".join(parts).lower()
    if any(word in text for word in ("death", "drowning", "suffocation", "fire", "burn", "entrapment", "fall")):
        return "critical"
    if any(word in text for word in ("lead", "laceration", "injury", "strangulation", "shock", "overheat")):
        return "high"
    if any(word in text for word in ("choking", "pinch", "tip-over", "chemical")):
        return "medium"
    return "low"


def _clean_html_text(fragment: str) -> str:
    text = re.sub(r"<br\\s*/?>", "\n", fragment, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_first(pattern: str, source: str) -> str:
    match = re.search(pattern, source, flags=re.I | re.S)
    if not match:
        return ""
    return _clean_html_text(match.group(1))


def _normalise_cpsc_alert(item: dict[str, Any]) -> dict[str, Any]:
    product_name = ", ".join(product.get("Name", "") for product in item.get("Products", []) if product.get("Name")) or "Consumer product"
    hazard = " ".join(hazard_item.get("Name", "") for hazard_item in item.get("Hazards", []) if hazard_item.get("Name")) or "Safety hazard published by CPSC."
    description = item.get("Description") or item.get("Title") or "CPSC recall notice."
    return {
        "source_name": "CPSC",
        "source_id": f"cpsc-live-{item['RecallID']}",
        "title": item.get("Title") or "CPSC recall",
        "alert_date": item.get("RecallDate") or now_iso(),
        "jurisdiction": "United States",
        "product_name": product_name,
        "hazard": hazard,
        "description": description,
        "source_url": item.get("URL") or "https://www.cpsc.gov/Recalls",
        "severity": _severity_from_text(item.get("Title", ""), hazard, description),
        "status": "new",
        "raw_payload": item,
    }


def _health_canada_search_results(term: str) -> list[dict[str, str]]:
    params = urllib.parse.urlencode({"search_api_fulltext": term, "f[0]": "cat:101"})
    url = f"https://recalls-rappels.canada.ca/en/search/site?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "NorthstarSafetyPrototype/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html_text = response.read().decode("utf-8", "ignore")
    pattern = re.compile(
        r'<div class="search-result views-row">.*?<a href="(?P<href>/en/alert-recall/[^"]+)"[^>]*>(?P<title>.*?)</a>.*?<span class="ar-type">(?P<kind>[^|<]+)\|\s*(?P<date>\d{4}-\d{2}-\d{2})',
        re.I | re.S,
    )
    results = []
    for match in pattern.finditer(html_text):
        results.append(
            {
                "href": urllib.parse.urljoin("https://recalls-rappels.canada.ca", match.group("href")),
                "title": _clean_html_text(match.group("title")),
                "kind": _clean_html_text(match.group("kind")),
                "date": match.group("date"),
            }
        )
    return results


def _fetch_health_canada_detail(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "NorthstarSafetyPrototype/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html_text = response.read().decode("utf-8", "ignore")
    title = _extract_first(r'<h1[^>]*>\s*<span>(.*?)</span>', html_text)
    product_name = _extract_first(r'<div id="product" class="field--label">Product</div>.*?field--item">(.*?)</div>', html_text)
    issue = _extract_first(r'<div id="issue" class="field--label">Issue</div>.*?field--item">(.*?)</div>', html_text)
    action = _extract_first(r'<div id="action" class="field--label">What to do</div>.*?field--item">(.*?)</div>', html_text)
    affected = _extract_first(r'field--name-field-affected-products-header[^>]*field--item">(.*?)</div>', html_text)
    updated_at = _extract_first(r'<div class="field--label">Last updated</div>.*?<time datetime="([^"]+)"', html_text)
    return {
        "title": title,
        "product_name": product_name,
        "issue": issue,
        "action": action,
        "affected": affected,
        "updated_at": updated_at,
        "url": url,
    }


def _normalise_health_canada_alert(result: dict[str, str], detail: dict[str, Any]) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(result["href"])
    source_slug = parsed.path.rstrip("/").split("/")[-1]
    issue_text = detail["issue"] or result["kind"] or "Health Canada consumer product notice."
    hazard = issue_text.split(" - ", 1)[-1] if " - " in issue_text else issue_text
    description_parts = [detail["action"], detail["affected"]]
    description = " ".join(part for part in description_parts if part).strip() or detail["title"] or result["title"]
    alert_date = (detail["updated_at"] or result["date"] or now_iso()).replace("T", " ").replace("Z", "")
    return {
        "source_name": "Health Canada",
        "source_id": f"health-canada-{source_slug}",
        "title": detail["title"] or result["title"] or "Health Canada recall",
        "alert_date": alert_date,
        "jurisdiction": "Canada",
        "product_name": detail["product_name"] or result["title"],
        "hazard": hazard,
        "description": description,
        "source_url": result["href"],
        "severity": _severity_from_text(detail["title"], issue_text, description),
        "status": "new",
        "raw_payload": {"search_result": result, "detail": detail},
    }


def ingest_live_cpsc(connection, limit_per_term: int = 6) -> dict[str, Any]:
    started_at = now_iso()
    if not settings.enable_live_cpsc:
        _record_sync_run(
            connection,
            source_name="cpsc-live",
            run_type="alert-ingest",
            status="skipped",
            records_processed=0,
            records_created=0,
            records_updated=0,
            notes="ENABLE_LIVE_CPSC is disabled.",
            started_at=started_at,
            completed_at=now_iso(),
        )
        return {
            "status": "skipped",
            "records_processed": 0,
            "records_created": 0,
            "records_updated": 0,
            "notes": "Live CPSC ingestion is disabled in environment settings.",
        }

    seen_ids: set[str] = set()
    created = 0
    updated = 0
    processed = 0
    for term in settings.cpsc_query_terms:
        encoded = urllib.parse.quote(term)
        url = f"https://www.saferproducts.gov/RestWebServices/Recall?ProductName={encoded}&format=json"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NorthstarSafetyPrototype/0.1"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload[:limit_per_term]:
            source_key = f"cpsc-live-{item['RecallID']}"
            if source_key in seen_ids:
                continue
            seen_ids.add(source_key)
            processed += 1
            result = upsert_alert(connection, _normalise_cpsc_alert(item))
            if result == "created":
                created += 1
            else:
                updated += 1

    recompute_matches_and_cases(connection)
    _record_sync_run(
        connection,
        source_name="cpsc-live",
        run_type="alert-ingest",
        status="completed",
        records_processed=processed,
        records_created=created,
        records_updated=updated,
        notes=f"Fetched live CPSC recalls for {len(settings.cpsc_query_terms)} query terms.",
        started_at=started_at,
        completed_at=now_iso(),
    )
    return {
        "status": "completed",
        "records_processed": processed,
        "records_created": created,
        "records_updated": updated,
        "notes": "Live CPSC recalls ingested and re-matched against the catalog.",
    }


def ingest_live_health_canada(connection, limit_per_term: int = 5) -> dict[str, Any]:
    started_at = now_iso()
    if not settings.enable_live_health_canada:
        _record_sync_run(
            connection,
            source_name="health-canada-live",
            run_type="alert-ingest",
            status="skipped",
            records_processed=0,
            records_created=0,
            records_updated=0,
            notes="ENABLE_LIVE_HEALTH_CANADA is disabled.",
            started_at=started_at,
            completed_at=now_iso(),
        )
        return {
            "status": "skipped",
            "records_processed": 0,
            "records_created": 0,
            "records_updated": 0,
            "notes": "Live Health Canada ingestion is disabled in environment settings.",
        }

    seen_ids: set[str] = set()
    created = 0
    updated = 0
    processed = 0
    for term in settings.health_canada_query_terms:
        for result in _health_canada_search_results(term)[:limit_per_term]:
            parsed = urllib.parse.urlparse(result["href"])
            source_slug = parsed.path.rstrip("/").split("/")[-1]
            source_key = f"health-canada-{source_slug}"
            if source_key in seen_ids:
                continue
            seen_ids.add(source_key)
            detail = _fetch_health_canada_detail(result["href"])
            processed += 1
            outcome = upsert_alert(connection, _normalise_health_canada_alert(result, detail))
            if outcome == "created":
                created += 1
            else:
                updated += 1

    recompute_matches_and_cases(connection)
    _record_sync_run(
        connection,
        source_name="health-canada-live",
        run_type="alert-ingest",
        status="completed",
        records_processed=processed,
        records_created=created,
        records_updated=updated,
        notes=f"Fetched live Health Canada consumer-product recalls for {len(settings.health_canada_query_terms)} query terms.",
        started_at=started_at,
        completed_at=now_iso(),
    )
    return {
        "status": "completed",
        "records_processed": processed,
        "records_created": created,
        "records_updated": updated,
        "notes": "Live Health Canada recalls ingested and re-matched against the catalog.",
    }
