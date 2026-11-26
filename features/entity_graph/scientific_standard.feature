@offline @unit
Feature: Scientific standards for toxicology limits, MRLs, nutrition, and dietary guidelines
  As a food and nutrition science layer
  I want a strict ScientificStandard model anchored by unit and EvidenceProvenance
  So that Indian statutory limits can be compared deterministically with EFSA, Codex, and IFCT 2017 benchmarks

  Scenario: Create a statutory MRL standard linked to a substance and food item
    Given a ScientificStandard with standard_id "std:in:fssai:mrl:chlorpyrifos:turmeric", standard_type "statutory_mrl", jurisdiction_iso "IN", substance_id "substance:cas:2921-88-2", food_item_id "item:ifct:E053", value 0.05, unit "mg/kg", effective_date "2024-01-01", and valid official_registry provenance
    Then the ScientificStandard is valid
    And its standard_type is "statutory_mrl"
    And its jurisdiction_iso is "IN"
    And its value is 0.05
    And its unit is "mg/kg"
    And its food_item_id is "item:ifct:E053"

  Scenario: Create a substance-wide toxicology reference limit without a food_item_id
    Given a ScientificStandard with standard_id "std:eu:efsa:adi:aflatoxin_b1", standard_type "toxicology_reference_limit", jurisdiction_iso "EU", substance_id "substance:cas:1162-65-8", value 0.002, unit "ug/kg", and valid peer_reviewed_science provenance
    Then the ScientificStandard is valid
    And its food_item_id is null
    And its effective_date is null
    And its provenance verification_tier is "peer_reviewed_science"

  Scenario Outline: Support all canonical standard_type values
    Given a ScientificStandard with standard_id "<standard_id>", standard_type "<standard_type>", jurisdiction_iso "<jurisdiction_iso>", substance_id "<substance_id>", value <value>, unit "<unit>", and valid provenance
    Then the ScientificStandard is valid
    And its standard_type is "<standard_type>"

    Examples:
      | standard_id                 | standard_type              | jurisdiction_iso | substance_id            | value | unit       |
      | std:codex:adi:532-32-1      | toxicology_reference_limit | WHO_CODEX        | substance:cas:532-32-1  | 5.0   | mg/kg      |
      | std:in:mrl:2921-88-2        | statutory_mrl              | IN               | substance:cas:2921-88-2 | 0.05  | mg/kg      |
      | std:in:ifct:E053:vitc       | nutrient_composition       | IN               | substance:cas:50-81-7   | 0.026 | g/100g     |
      | std:in:icmr:rda:vitc        | dietary_guideline          | IN               | substance:cas:50-81-7   | 80.0  | mg/day     |

  Scenario: Reject an unsupported standard_type
    When I attempt to create a ScientificStandard with standard_type "opinion_score"
    Then a ValidationError is raised

  Scenario: Enforce strict typing and frozen immutability on ScientificStandard
    Given a valid ScientificStandard with value 0.05 and unit "mg/kg"
    When I attempt to mutate its value
    Then a ValidationError is raised
    When I attempt to create a ScientificStandard with string "0.05" as value
    Then a ValidationError is raised
    When I attempt to create a ScientificStandard without provenance
    Then a ValidationError is raised
