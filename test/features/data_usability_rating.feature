@data_usability_rating
Feature: Data usability rating

    Scenario: As an admin user of my organisation, when I create a dataset with a HTML resource, I can verify the score is 0
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "HTML" resource file "html_resource.html"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"


    Scenario: As an admin user of my organisation, when I create a dataset with an open license and TXT resource, I can verify the score is 1
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "TXT" resource file "txt_resource.txt"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"


    Scenario: As an admin user of my organisation, when I create a dataset with an open license and XLS resource, I can verify the score is 2
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "XLS" resource file "xls_resource.xls"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"


    Scenario: As an admin user of my organisation, when I create a dataset with an open license and a CSV resource, I can verify the score is 3
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "CSV" resource file "csv_resource.csv"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"


    Scenario: As an admin user of my organisation, when I create a dataset with an open license and a JSON resource, I can verify the score is 3
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "JSON" resource file "test-resource_schema.json"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"


    Scenario: As an admin user of my organisation, when I create a dataset with an open license and a RDF resource, I can verify the score is 4
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "RDF" resource file "rdf_resource.rdf"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//h2[contains(text(), 'Openness')]"
