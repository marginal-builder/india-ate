@offline @unit
Feature: Food items linked to FoodOn, IFCT 2017, GTIN, and supply-chain actors
  As an open food entity graph
  I want a FoodItem model linking dishes, staples, packaged products, and supplements to FoodOn, IFCT 2017, GTIN barcodes, and manufacturers
  So that consumers can trace both raw nutrition and contract-manufactured packaged foods

  Scenario: Create a raw staple linked to FoodOn URI and ICMR-NIN IFCT 2017 code
    Given a FoodItem with item_id "item:ifct:E053", canonical_name "Turmeric powder", item_kind "raw_staple", foodon_uri "http://purl.obolibrary.org/obo/FOODON_03301414", and ifct_code "E053"
    Then the FoodItem is valid
    And its item_kind is "raw_staple"
    And its foodon_uri is "http://purl.obolibrary.org/obo/FOODON_03301414"
    And its ifct_code is "E053"
    And its gtin_barcode is null
    And its manufacturer_premises_ids is empty
    And its marketer_actor_ids is empty

  Scenario: Create a packaged product with GTIN barcode and co-packer/marketer links
    Given a FoodItem with item_id "item:gtin:8901234567890", canonical_name "Masala Oats 500g", item_kind "packaged_product", gtin_barcode "8901234567890", manufacturer_premises_ids containing "actor:in:fssai:10013022000417", and marketer_actor_ids containing "actor:in:fssai:10411012000075"
    Then the FoodItem is valid
    And its item_kind is "packaged_product"
    And its gtin_barcode is "8901234567890"
    And manufacturer_premises_ids contains "actor:in:fssai:10013022000417"
    And marketer_actor_ids contains "actor:in:fssai:10411012000075"

  Scenario: Support menu_dish and supplement item kinds
    Given a FoodItem with item_id "item:dish:paneer_tikka", canonical_name "Paneer Tikka", and item_kind "menu_dish"
    And a FoodItem with item_id "item:supp:whey_01", canonical_name "Whey Protein Isolate", and item_kind "supplement"
    Then both FoodItems are valid

  Scenario: Reject an unsupported item_kind on FoodItem
    When I attempt to create a FoodItem with item_kind "unclassified_snack"
    Then a ValidationError is raised

  Scenario: Enforce strict and frozen immutability on FoodItem
    Given a valid FoodItem with item_id "item:ifct:E053" and canonical_name "Turmeric powder"
    When I attempt to mutate its canonical_name
    Then a ValidationError is raised
    When I attempt to create a FoodItem with integer 42 as canonical_name
    Then a ValidationError is raised
