@offline @unit
Feature: Substances keyed by CAS, PubChem CID, and INS/E-number
  As a food and nutrition science layer
  I want a strict Substance model covering nutrients, additives, contaminants, microbes, and allergens
  So that chemical and biological hazards and nutrients have unambiguous global identifiers

  Scenario: Create an additive Substance with CAS, PubChem CID, and INS/E-number
    Given a Substance with substance_id "substance:cas:532-32-1", canonical_name "Sodium Benzoate", substance_class "additive", cas_number "532-32-1", pubchem_cid "517055", and ins_e_number "INS 211"
    Then the Substance is valid
    And its substance_class is "additive"
    And its cas_number is "532-32-1"
    And its pubchem_cid is "517055"
    And its ins_e_number is "INS 211"

  Scenario Outline: Support all canonical substance_class categories
    Given a Substance with substance_id "<substance_id>", canonical_name "<canonical_name>", substance_class "<substance_class>", and cas_number <cas_number>
    Then the Substance is valid
    And its substance_class is "<substance_class>"

    Examples:
      | substance_id               | canonical_name     | substance_class   | cas_number    |
      | substance:cas:50-81-7      | Ascorbic acid      | nutrient          | "50-81-7"     |
      | substance:cas:532-32-1     | Sodium Benzoate    | additive          | "532-32-1"    |
      | substance:cas:2921-88-2    | Chlorpyrifos       | pesticide_residue | "2921-88-2"   |
      | substance:cas:7439-92-1    | Lead               | heavy_metal       | "7439-92-1"   |
      | substance:cas:1162-65-8    | Aflatoxin B1       | mycotoxin         | "1162-65-8"   |
      | substance:bio:salmonella   | Salmonella spp.    | microbe           | null          |
      | substance:allergen:peanut  | Peanut protein     | allergen          | null          |

  Scenario: Default optional chemical identifiers to null
    Given a Substance with substance_id "substance:allergen:gluten", canonical_name "Gluten", and substance_class "allergen"
    Then cas_number is null
    And pubchem_cid is null
    And ins_e_number is null

  Scenario: Reject an unsupported substance_class
    When I attempt to create a Substance with substance_class "unknown_chemical_group"
    Then a ValidationError is raised

  Scenario: Enforce strict and frozen immutability on Substance
    Given a valid Substance with substance_id "substance:cas:532-32-1" and canonical_name "Sodium Benzoate"
    When I attempt to mutate its cas_number
    Then a ValidationError is raised
    When I attempt to create a Substance with integer 532 as cas_number
    Then a ValidationError is raised
