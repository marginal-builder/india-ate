@offline @unit
Feature: FSSAI 14-digit offline decoder
  As a consumer safety application
  I want to decode any 14-digit FSSAI license or registration number offline
  So that I can determine license tier, authority scope, state, registration year, officer code, and serial with zero network calls

  Scenario: Decode a Central License under Maharashtra DO (RO Mumbai)
    Given the FSSAI number "10013022000417"
    When I call decode_offline()
    Then the tier is "license"
    And pre_inspection_exempt_post_apr2026 is false
    And the authority_scope is "central"
    And the state_code is "00"
    And the state_name is "Central"
    And the registration_year is 2013
    And the officer_code is "022"
    And the central_regional_office is "RO Mumbai"
    And the officer_jurisdiction_state is "Maharashtra"
    And the serial is "000417"

  Scenario: Decode a Bihar State License from the official FSSAI circular
    Given the FSSAI number "10411012000075"
    When I call decode_offline()
    Then the tier is "license"
    And pre_inspection_exempt_post_apr2026 is false
    And the authority_scope is "state_or_ut"
    And the state_code is "04"
    And the state_name is "Bihar"
    And the registration_year is 2011
    And the officer_code is "012"
    And the central_regional_office is null
    And the serial is "000075"

  Scenario: Decode an Uttar Pradesh Basic Registration from the official FSSAI circular
    Given the FSSAI number "22711126011608"
    When I call decode_offline()
    Then the tier is "basic_registration"
    And pre_inspection_exempt_post_apr2026 is true
    And the authority_scope is "state_or_ut"
    And the state_code is "27"
    And the state_name is "Uttar Pradesh"
    And the registration_year is 2011
    And the officer_code is "126"
    And the central_regional_office is null
    And the serial is "011608"

  Scenario: Decode a Central License under Jharkhand DO (RO Kolkata)
    Given the FSSAI number "10011034002374"
    When I call decode_offline()
    Then the tier is "license"
    And pre_inspection_exempt_post_apr2026 is false
    And the authority_scope is "central"
    And the state_code is "00"
    And the state_name is "Central"
    And the registration_year is 2011
    And the officer_code is "034"
    And the central_regional_office is "RO Kolkata"
    And the officer_jurisdiction_state is "Jharkhand"
    And the serial is "002374"

  Scenario: Decode post-2011 State and UT codes for Telangana (36) and Ladakh (37)
    Given the FSSAI number "23624001000123"
    When I call decode_offline()
    Then the tier is "basic_registration"
    And pre_inspection_exempt_post_apr2026 is true
    And the authority_scope is "state_or_ut"
    And the state_code is "36"
    And the state_name is "Telangana"
    And the registration_year is 2024
    And the officer_code is "001"
    And the serial is "000123"

  Scenario: Decode Ladakh UT license code (37)
    Given the FSSAI number "13724001000456"
    When I call decode_offline()
    Then the tier is "license"
    And pre_inspection_exempt_post_apr2026 is false
    And the authority_scope is "state_or_ut"
    And the state_code is "37"
    And the state_name is "Ladakh"
    And the registration_year is 2024
    And the officer_code is "001"
    And the serial is "000456"

  Scenario: Trim surrounding whitespace before decoding
    Given the FSSAI number " 10013022000417 "
    When I call decode_offline()
    Then the tier is "license"
    And the state_code is "00"
    And the serial is "000417"

  Scenario: IndiaFSSAI14 inherits polymorphic RegulatoryIdentifier defaults
    Given an IndiaFSSAI14 identifier with raw_value "10013022000417"
    Then its jurisdiction_iso is "IN"
    And its scheme is "IN_FSSAI_14"
    And calling decode_offline() on the base RegulatoryIdentifier raises NotImplementedError

  Scenario: Reject a non-14-digit input
    Given the FSSAI number "12345"
    When I call decode_offline()
    Then a ValueError is raised
    And the error message contains "14-digit"

  Scenario: Reject a 14-character non-numeric input
    Given the FSSAI number "1001302200041A"
    When I call decode_offline()
    Then a ValueError is raised
    And the error message contains "14-digit"

  Scenario: Reject an invalid license tier digit
    Given the FSSAI number "30013022000417"
    When I call decode_offline()
    Then a ValueError is raised
    And the error message contains "tier"

  Scenario: Reject an unknown state or UT code above 37
    Given the FSSAI number "13824001000001"
    When I call decode_offline()
    Then a ValueError is raised
    And the error message contains "state"

  Scenario: Decode via CLI india-ate decode returns structured JSON offline
    When I run the CLI command "india-ate decode 10013022000417"
    Then the CLI exit code is 0
    And the CLI stdout is valid JSON
    And the JSON field "tier" equals "license"
    And the JSON field "authority_scope" equals "central"
    And the JSON field "state_code" equals "00"
    And the JSON field "state_name" equals "Central"
    And the JSON field "registration_year" equals 2013
    And the JSON field "officer_code" equals "022"
    And the JSON field "serial" equals "000417"
    And the JSON field "pre_inspection_exempt_post_apr2026" equals false

  Scenario: CLI india-ate decode fails cleanly on invalid FSSAI ID
    When I run the CLI command "india-ate decode 12345"
    Then the CLI exit code is non-zero
    And the CLI output contains "14-digit"
