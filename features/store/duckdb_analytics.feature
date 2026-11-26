@offline @integration
Feature: DuckDB analytical queries and Parquet snapshot export
  As a food safety researcher or consumer analytics backend
  I want Parquet snapshot exports and DuckDB analytical queries over the entity graph
  So that ghost-brand clusters by pin code and enforcement trends can be aggregated offline at zero cost

  Scenario: Export FoodPremises, BrandListing, and AuthoritativeEvent to Parquet snapshots
    Given an initialized SQLite store populated with FoodPremises, BrandListing, and AuthoritativeEvent records
    When I export Parquet snapshots to a snapshot directory using DuckDB
    Then non-empty Parquet files are created for food_premises, brand_listings, and authoritative_events

  Scenario: Query ghost-brand cluster counts by postal_code via DuckDB over Parquet
    Given Parquet snapshots containing:
      | premises_entity_id           | postal_code | listing_id         | display_name          |
      | actor:in:fssai:23624001000123 | 500081      | listing:swiggy:101 | Royal Biryani Kitchen |
      | actor:in:fssai:23624001000123 | 500081      | listing:zomato:202 | Midnight Bowl Co      |
      | actor:in:fssai:23624001000123 | 500081      | listing:swiggy:303 | Nawab Express         |
      | actor:in:fssai:10013022000417 | 400001      | listing:ondc:404   | Mumbai Bakery         |
    When I run the DuckDB ghost-brand cluster analytics query grouped by postal_code
    Then postal_code "500081" reports 1 premises_count and 3 brand_listing_count
    And postal_code "400001" reports 1 premises_count and 1 brand_listing_count

  Scenario: Query enforcement event counts by event_type and status via DuckDB
    Given Parquet snapshots containing 2 "enforcement_raid_or_suspension" events with status "Suspended" and 1 "hygiene_audit" event with status "Active"
    When I run the DuckDB enforcement summary query over the authoritative_events Parquet snapshot
    Then "enforcement_raid_or_suspension" with status "Suspended" has count 2
    And "hygiene_audit" with status "Active" has count 1
