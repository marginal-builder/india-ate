@offline @integration
Feature: SQLite runtime persistence store for FoodPremises, BrandListing, and AuthoritativeEvent
  As a local-first entity graph runtime
  I want parameterized SQLite persistence for FoodPremises, BrandListing, and AuthoritativeEvent
  So that I can query ghost-brand clusters by FSSAI ID and discover nearby premises by pin code safely

  Scenario: Save and retrieve a FoodPremises by entity_id and by 14-digit FSSAI ID
    Given an initialized SQLite store
    And a FoodPremises with entity_id "actor:in:fssai:10013022000417", legal_name "Acme Foods Pvt Ltd", premises_type "co_packer_factory", postal_code "400001", city "Mumbai", state "Maharashtra", and IndiaFSSAI14 "10013022000417"
    When I save the FoodPremises to the SQLite store
    And I get the FoodPremises by entity_id "actor:in:fssai:10013022000417"
    Then the retrieved FoodPremises equals the saved FoodPremises
    When I get the FoodPremises by FSSAI ID "10013022000417"
    Then its entity_id is "actor:in:fssai:10013022000417"
    And its postal_code is "400001"

  Scenario: Save and retrieve BrandListing and AuthoritativeEvent records
    Given an initialized SQLite store with saved FoodPremises "actor:in:fssai:23624001000123"
    And a BrandListing "listing:swiggy:101" linked to premises_entity_id "actor:in:fssai:23624001000123"
    And an AuthoritativeEvent "evt:tgsafe:raid:2026-42" targeting "actor:in:fssai:23624001000123" with status "Suspended"
    When I save the BrandListing and AuthoritativeEvent to the SQLite store
    Then retrieving BrandListings for "actor:in:fssai:23624001000123" returns 1 listing with listing_id "listing:swiggy:101"
    And retrieving AuthoritativeEvents for "actor:in:fssai:23624001000123" returns 1 event with status "Suspended"

  Scenario: Query ghost-brand cluster by 14-digit FSSAI ID
    Given an initialized SQLite store
    And a FoodPremises with entity_id "actor:in:fssai:23624001000123", IndiaFSSAI14 "23624001000123", and postal_code "500081"
    And 3 BrandListings ("Royal Biryani Kitchen", "Midnight Bowl Co", "Nawab Express") all linked to premises_entity_id "actor:in:fssai:23624001000123"
    When I query the ghost-brand cluster for FSSAI ID "23624001000123"
    Then the cluster returns the FoodPremises "actor:in:fssai:23624001000123"
    And the cluster contains all 3 BrandListings

  Scenario: Query nearby FoodPremises by pin code
    Given an initialized SQLite store
    And a FoodPremises "actor:in:fssai:23624001000123" in postal_code "500081"
    And a FoodPremises "actor:in:fssai:13624001000999" in postal_code "500081"
    And a FoodPremises "actor:in:fssai:10013022000417" in postal_code "400001"
    When I query nearby FoodPremises for postal_code "500081"
    Then 2 FoodPremises records are returned
    And the returned entity_ids do not include "actor:in:fssai:10013022000417"

  Scenario: Parameterized queries resist SQL injection payloads safely
    Given an initialized SQLite store containing FoodPremises "actor:in:fssai:10013022000417"
    When I query the ghost-brand cluster for FSSAI ID "' OR '1'='1'; DROP TABLE food_premises; --"
    Then an empty result is returned without raising a database error
    When I query nearby FoodPremises for postal_code "' OR '1'='1'; DROP TABLE food_premises; --"
    Then 0 FoodPremises records are returned
    And FoodPremises "actor:in:fssai:10013022000417" still exists in the SQLite store
