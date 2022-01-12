@data_usability_rating
Feature: Data usability rating

    Scenario: As an organisation admin, when I create a dataset with an open license and HTML resource, I can verify the score is 0
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "HTML" resource file "html_resource.html"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 0
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 0


    Scenario: As an organisation admin, when I create a dataset with an open license and TXT resource, I can verify the score is 1
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "TXT" resource file "txt_resource.txt"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 1
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 1


    Scenario: As an organisation admin, when I create a dataset with an open license and XLS resource, I can verify the score is 2
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "XLS" resource file "xls_resource.xls"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 2
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 2


    Scenario: As an organisation admin, when I create a dataset with an open license and CSV resource, I can verify the score is 3
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "CSV" resource file "csv_resource.csv"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 3
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 3


    Scenario: As an organisation admin, when I create a dataset with an open license and JSON resource, I can verify the score is 3
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "JSON" resource file "test-resource_schema.json"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 3
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 3


    Scenario: As an organisation admin, when I create a dataset with an open license and RDF resource, I can verify the score is 4
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and "RDF" resource file "rdf_resource.rdf"
        Then I wait for 10 seconds
        When I reload
        Then I should see data usability rating 4
        When I click the link with text that contains "Test resource"
        Then I should see data usability rating 4
