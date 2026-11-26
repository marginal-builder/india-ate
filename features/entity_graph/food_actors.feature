@offline @unit
Feature: Food actors, premises, brand listings, and evidence provenance
  As an open food entity graph
  I want immutable, strictly validated FoodActor, FoodPremises, BrandListing, and EvidenceProvenance models
  So that every consumer storefront maps traceably N:1 to a physical premises with verified provenance

  Scenario: Create a valid EvidenceProvenance record
    Given an EvidenceProvenance with source_name "FoSCoS Recall Portal", source_url "https://foscos.fssai.gov.in/recalls", retrieved_at "2026-04-01T10:00:00Z", content_sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", and verification_tier "official_registry"
    Then the EvidenceProvenance is valid
    And its verification_tier is "official_registry"

  Scenario: Reject invalid verification_tier or unverified URL on EvidenceProvenance
    When I attempt to create an EvidenceProvenance with verification_tier "social_media_rumor"
    Then a ValidationError is raised
    When I attempt to create an EvidenceProvenance with source_url "not-a-valid-url"
    Then a ValidationError is raised

  Scenario: Enforce strict and frozen immutability on EvidenceProvenance
    Given a valid EvidenceProvenance record
    When I attempt to mutate its content_sha256 field
    Then a ValidationError is raised
    When I attempt to create an EvidenceProvenance with integer 123 as source_name
    Then a ValidationError is raised

  Scenario: Create a FoodActor with regulatory IDs and provenance
    Given a FoodActor with entity_id "actor:in:fssai:10013022000417", legal_name "Acme Foods Pvt Ltd", jurisdiction_iso "IN", regulatory_ids containing IndiaFSSAI14 "10013022000417", and valid official_registry provenance
    Then the FoodActor is valid
    And its regulatory_ids has length 1
    And its provenance has length 1

  Scenario: FoodPremises substitutes cleanly for FoodActor across all premises types
    Given a FoodPremises with entity_id "actor:in:fssai:23624001000123", legal_name "Deccan Cloud Hospitality", jurisdiction_iso "IN", premises_type "cloud_kitchen", address "Plot 14, Madhapur", postal_code "500081", city "Hyderabad", state "Telangana", lat 17.4486, lon 78.3908, and valid provenance
    Then the FoodPremises is an instance of FoodActor
    And its premises_type is "cloud_kitchen"
    And its postal_code is "500081"

  Scenario: Reject unsupported premises_type on FoodPremises
    When I attempt to create a FoodPremises with premises_type "unlicensed_pushcart"
    Then a ValidationError is raised

  Scenario: Default optional location fields on FoodPremises to null
    Given a FoodPremises with only required fields and premises_type "dark_store"
    Then address is null
    And postal_code is null
    And city is null
    And state is null
    And lat is null
    And lon is null

  Scenario: Map multiple BrandListings N:1 to one FoodPremises to expose a ghost-brand cluster
    Given a FoodPremises with entity_id "actor:in:fssai:23624001000123" and postal_code "500081"
    And a BrandListing "listing:swiggy:101" with display_name "Royal Biryani Kitchen", platform "swiggy", and premises_entity_id "actor:in:fssai:23624001000123"
    And a BrandListing "listing:zomato:202" with display_name "Midnight Bowl Co", platform "zomato", and premises_entity_id "actor:in:fssai:23624001000123"
    And a BrandListing "listing:swiggy:303" with display_name "Nawab Express", platform "swiggy", and premises_entity_id "actor:in:fssai:23624001000123"
    When I group those BrandListings by premises_entity_id
    Then premises_entity_id "actor:in:fssai:23624001000123" has 3 distinct storefront display names in its ghost-brand cluster

  Scenario: Reject unsupported platform on BrandListing
    When I attempt to create a BrandListing with platform "unknown_delivery_app"
    Then a ValidationError is raised

  Scenario: Enforce strict and frozen immutability on FoodActor, FoodPremises, and BrandListing
    Given a valid FoodActor, FoodPremises, and BrandListing
    When I attempt to mutate legal_name on FoodActor
    Then a ValidationError is raised
    When I attempt to mutate premises_type on FoodPremises
    Then a ValidationError is raised
    When I attempt to mutate display_name on BrandListing
    Then a ValidationError is raised
    When I attempt to create a BrandListing with integer 999 as display_name
    Then a ValidationError is raised
