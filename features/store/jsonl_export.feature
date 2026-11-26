@offline @integration
Feature: Open-data JSONL dataset export and import round-trip
  As an open-source public data project
  I want deterministic line-delimited JSON (.jsonl) export and import across all entity types
  So that the canonical food safety graph can be versioned in Git and shared transparently

  Scenario: Export and re-import entities via JSONL round-trip with zero data loss
    Given a dataset containing FoodPremises, BrandListing, FoodItem, Substance, ScientificStandard, and AuthoritativeEvent records
    When I export the dataset to a ".jsonl" file
    Then every line in the ".jsonl" file is valid UTF-8 JSON
    And the line count equals the total number of exported records
    When I import the ".jsonl" file back into Pydantic entity models
    Then every reconstructed entity equals the original entity including nested EvidenceProvenance and RegulatoryIdentifier

  Scenario: Export and import an empty dataset cleanly
    Given an empty dataset with 0 records
    When I export the dataset to a ".jsonl" file
    Then the ".jsonl" file contains 0 lines
    When I import the empty ".jsonl" file
    Then 0 records are returned

  Scenario: Reject malformed JSONL input on import without silent corruption
    Given a ".jsonl" file containing a truncated or invalid JSON line
    When I attempt to import the ".jsonl" file
    Then a ValueError or ValidationError is raised
