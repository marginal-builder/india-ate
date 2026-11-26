@offline @unit
Feature: Authoritative enforcement events and BaseSourceAdapter ingestion contract
  As an open accountability entity graph
  I want immutable AuthoritativeEvent records and a deterministic BaseSourceAdapter interface
  So that recalls, hygiene audits, raids, suspensions, and grievances trace strictly to official records without hallucination

  Scenario: Create a food recall AuthoritativeEvent with batch_or_lot_no
    Given an AuthoritativeEvent with event_id "evt:foscos:recall:2026-001", event_type "food_recall", target_entity_id "item:gtin:8901234567890", jurisdiction_iso "IN", event_date "2026-03-20", status "Initiated", batch_or_lot_no "LOT-MH-2026-09", verbatim_summary "Voluntary recall initiated due to elevated aflatoxin levels in batch LOT-MH-2026-09.", and valid official_registry provenance
    Then the AuthoritativeEvent is valid
    And its event_type is "food_recall"
    And its status is "Initiated"
    And its batch_or_lot_no is "LOT-MH-2026-09"

  Scenario: Create a hygiene audit AuthoritativeEvent targeting a FoodPremises
    Given an AuthoritativeEvent with event_id "evt:hygiene:2026-8824", event_type "hygiene_audit", target_entity_id "actor:in:fssai:10013022000417", jurisdiction_iso "IN", event_date "2026-02-14", status "Active", verbatim_summary "FSSAI Hygiene Rating audit completed with rating 4 out of 5.", and valid official_registry provenance
    Then the AuthoritativeEvent is valid
    And its event_type is "hygiene_audit"
    And its batch_or_lot_no is null

  Scenario: Create an enforcement raid or suspension AuthoritativeEvent
    Given an AuthoritativeEvent with event_id "evt:tgsafe:raid:2026-42", event_type "enforcement_raid_or_suspension", target_entity_id "actor:in:fssai:23624001000123", jurisdiction_iso "IN", event_date "2026-04-02", status "Suspended", verbatim_summary "License suspended by state food safety task force for unhygienic kitchen premises.", and valid official_registry provenance
    Then the AuthoritativeEvent is valid
    And its status is "Suspended"

  Scenario: Create a grievance ticket AuthoritativeEvent
    Given an AuthoritativeEvent with event_id "evt:grievance:2026-991", event_type "grievance_ticket", target_entity_id "actor:in:fssai:23624001000123", jurisdiction_iso "IN", event_date "2026-04-05", status "Escalated_15d", verbatim_summary "Consumer food safety grievance escalated after 15 days without resolution.", and valid user_verified_snapshot provenance
    Then the AuthoritativeEvent is valid
    And its event_type is "grievance_ticket"
    And its status is "Escalated_15d"

  Scenario Outline: Support all canonical event_type values
    Given an AuthoritativeEvent with event_id "<event_id>", event_type "<event_type>", target_entity_id "actor:in:fssai:10013022000417", jurisdiction_iso "IN", event_date "2026-04-01", status "<status>", verbatim_summary "Verbatim authoritative summary.", and valid official_registry provenance
    Then the AuthoritativeEvent is valid
    And its event_type is "<event_type>"

    Examples:
      | event_id        | event_type                     | status        |
      | evt:lic:001     | license_status_snapshot        | Active        |
      | evt:audit:001   | hygiene_audit                  | Active        |
      | evt:recall:001  | food_recall                    | Initiated     |
      | evt:raid:001    | enforcement_raid_or_suspension | Suspended     |
      | evt:lab:001     | lab_test_result                | Active        |
      | evt:griev:001   | grievance_ticket               | Escalated_15d |

  Scenario: Reject an unsupported event_type and enforce frozen immutability
    When I attempt to create an AuthoritativeEvent with event_type "unverified_rumor"
    Then a ValidationError is raised
    Given a valid AuthoritativeEvent with status "Active"
    When I attempt to mutate its status field
    Then a ValidationError is raised

  Scenario: BaseSourceAdapter cannot be instantiated directly without implementing abstract methods
    When I inspect BaseSourceAdapter
    Then it defines abstract methods fetch, parse, and validate_and_emit
    And attempting to instantiate BaseSourceAdapter directly raises TypeError

  Scenario: Concrete BaseSourceAdapter emits valid records and quarantines ambiguous records deterministically
    Given a concrete offline adapter implementing BaseSourceAdapter for source_name "FoSCoS Recall Portal" and jurisdiction_iso "IN"
    And raw fixture bytes containing one valid recall record with valid provenance and one ambiguous record missing content_sha256 and target_entity_id
    When I run fetch(), parse(raw), and validate_and_emit(records)
    Then 1 valid AuthoritativeEvent model is emitted
    And the ambiguous record is quarantined rather than guessed or coerced into a live entity
