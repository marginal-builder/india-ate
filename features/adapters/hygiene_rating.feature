@offline
Feature: FSSAI Hygiene Rating Adapter, Quarantine, SQLite Batch Persistence, and CLI Ingestion
  As an open food accountability entity graph
  I want to ingest FSSAI Hygiene Rating HTML and JSON snapshots deterministically with strict quarantine
  So that every audited FoodPremises and AuthoritativeEvent traces to immutable official provenance without guessing

  @unit
  Scenario: Enforce strict and frozen immutability on QuarantinedRecord and IngestionBatch
    Given a QuarantinedRecord with source_name "FSSAI Hygiene Rating Portal", raw_record containing fssai_id "12345", reason "Invalid 14-digit FSSAI ID", and quarantined_at "2026-04-01T10:00:00Z"
    Then the QuarantinedRecord is valid
    When I attempt to mutate the reason field on the QuarantinedRecord
    Then a ValidationError is raised
    When I attempt to create a QuarantinedRecord with integer 123 as source_name
    Then a ValidationError is raised
    Given an empty IngestionBatch with default fields
    Then its entities list is empty
    And its quarantined list is empty
    When I attempt to mutate the entities field on the IngestionBatch
    Then a ValidationError is raised

  @unit
  Scenario: Parse a valid HTML hygiene rating snapshot and emit FoodPremises and AuthoritativeEvent with exact provenance
    Given a deterministic offline HttpFetcher returning an HTML snapshot for "FSSAI Hygiene Rating Portal" from URL "https://hygiene.fssai.gov.in/snapshot"
    And the HTML snapshot contains a valid eatery row with fssai_id "10013022000417", legal_name "Acme Foods Pvt Ltd", premises_type "restaurant", address "12 MG Road", postal_code "400001", city "Mumbai", state "Maharashtra", rating "5/5", and audit_date "2026-02-14"
    When I run HygieneRatingAdapter fetch(), parse(raw), and validate_and_emit_batch(records)
    Then the IngestionBatch contains 1 FoodPremises and 1 AuthoritativeEvent
    And the IngestionBatch quarantined list is empty
    And the emitted FoodPremises has entity_id "actor:in:fssai:10013022000417" and legal_name "Acme Foods Pvt Ltd"
    And the emitted FoodPremises has regulatory_ids containing IndiaFSSAI14 "10013022000417"
    And the emitted AuthoritativeEvent has event_type "hygiene_audit", target_entity_id "actor:in:fssai:10013022000417", status "5/5", and event_date "2026-02-14"
    And both emitted entities carry EvidenceProvenance with verification_tier "official_registry" and content_sha256 matching the SHA-256 of the raw snapshot bytes

  @unit
  Scenario: Parse a valid JSON hygiene rating snapshot and emit FoodPremises and AuthoritativeEvent
    Given a deterministic offline HttpFetcher returning a JSON snapshot for "FSSAI Hygiene Rating Portal" from URL "https://hygiene.fssai.gov.in/api/ratings"
    And the JSON snapshot contains a valid eatery row with fssai_id "22711126011608", legal_name "Awadh Kitchens", premises_type "restaurant", address "45 Hazratganj", postal_code "226001", city "Lucknow", state "Uttar Pradesh", rating "4/5", and audit_date "2026-03-10"
    When I run HygieneRatingAdapter fetch(), parse(raw), and validate_and_emit_batch(records)
    Then the IngestionBatch contains 1 FoodPremises and 1 AuthoritativeEvent
    And the IngestionBatch quarantined list is empty
    And the emitted FoodPremises has entity_id "actor:in:fssai:22711126011608" and state "Uttar Pradesh"
    And the emitted AuthoritativeEvent has event_type "hygiene_audit", target_entity_id "actor:in:fssai:22711126011608", and status "4/5"
    And both emitted entities carry EvidenceProvenance with verification_tier "official_registry" and content_sha256 matching the SHA-256 of the raw snapshot bytes

  @unit
  Scenario Outline: Quarantine invalid or ambiguous hygiene rating rows without guessing
    Given a deterministic offline HttpFetcher returning a JSON snapshot with 1 invalid row having fssai_id "<fssai_id>", legal_name "<legal_name>", rating "<rating>", and audit_date "<audit_date>"
    When I run HygieneRatingAdapter fetch(), parse(raw), and validate_and_emit_batch(records)
    Then the IngestionBatch entities list is empty
    And the IngestionBatch quarantined list has length 1
    And the quarantined record has source_name "FSSAI Hygiene Rating Portal"
    And the quarantined record reason contains "<expected_reason>"
    And the quarantined record preserves the original raw_record

    Examples:
      | fssai_id       | legal_name        | rating | audit_date | expected_reason |
      |                | Missing ID Bistro | 4/5    | 2026-02-14 | fssai           |
      | 12345          | Short ID Cafe     | 4/5    | 2026-02-14 | 14-digit        |
      | १००१३०२२०००४१७ | Devanagari Digits | 4/5    | 2026-02-14 | ASCII           |
      | 10411012000075 |                   | 4/5    | 2026-02-14 | legal_name      |
      | 10411012000075 | No Rating Dhaba   |        | 2026-02-14 | rating          |
      | 10411012000075 | No Date Kitchen   | 3/5    |            | audit_date      |

  @unit
  Scenario: Mixed snapshot emits valid rows and quarantines malformed rows independently
    Given a deterministic offline HttpFetcher returning a JSON snapshot with 1 valid row for fssai_id "10411012000075" and 1 invalid row with fssai_id "999"
    When I run HygieneRatingAdapter fetch(), parse(raw), and validate_and_emit_batch(records)
    Then the IngestionBatch contains 1 FoodPremises and 1 AuthoritativeEvent for "actor:in:fssai:10411012000075"
    And the IngestionBatch quarantined list has length 1 for raw fssai_id "999"

  @unit
  Scenario: Injectable HttpFetcher protocol prevents real network calls during offline ingestion
    Given a custom HttpFetcher stub that records requested URLs and returns deterministic bytes without network access
    When HygieneRatingAdapter.fetch() is invoked
    Then the custom HttpFetcher receives the configured portal URL
    And zero external network connections are attempted
    And the returned bytes match the stub response verbatim

  @integration
  Scenario: SQLiteStore save_ingestion_batch persists FoodPremises, AuthoritativeEvent, and QuarantinedRecord atomically
    Given an initialized SQLiteStore
    And an IngestionBatch containing FoodPremises "actor:in:fssai:10011034002374", AuthoritativeEvent "evt:hygiene:10011034002374:2026-03-01", and 1 QuarantinedRecord for raw fssai_id "bad-id"
    When I call save_ingestion_batch on the SQLiteStore
    Then getting FoodPremises by FSSAI ID "10011034002374" returns "actor:in:fssai:10011034002374"
    And retrieving AuthoritativeEvents for "actor:in:fssai:10011034002374" returns 1 event with event_type "hygiene_audit"
    And list_quarantined on the SQLiteStore returns 1 QuarantinedRecord with reason preserved

  @integration
  Scenario: CLI ingests a local hygiene rating snapshot and prints a Fact Receipt JSON on lookup
    Given a local HTML hygiene rating snapshot file containing valid eatery "10013022000417" and 1 malformed row
    And a SQLiteStore at a temporary database path with a BrandListing "listing:swiggy:77" linked to "actor:in:fssai:10013022000417"
    When I run the CLI command "india-ate ingest hygiene --from-file <snapshot> --db <path>"
    Then the CLI exits with status code 0
    And the CLI output reports 1 premises ingested, 1 event ingested, and 1 record quarantined
    When I run the CLI command "india-ate lookup 10013022000417 --db <path>"
    Then the CLI exits with status code 0
    And the stdout is valid Fact Receipt JSON containing decoded IndiaFSSAI14 fields for "10013022000417"
    And the Fact Receipt JSON includes the stored FoodPremises "actor:in:fssai:10013022000417"
    And the Fact Receipt JSON includes the BrandListing "listing:swiggy:77"
    And the Fact Receipt JSON includes the hygiene_audit AuthoritativeEvent for "actor:in:fssai:10013022000417"
