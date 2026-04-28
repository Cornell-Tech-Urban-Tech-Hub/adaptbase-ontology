# Fact Table Climate Adaptation README

This document provides a detailed overview of the columns in the `fact_table_climate_adaptation.csv` file. This dataset contains information about climate adaptation goals, actions, and projects reported by various cities.

**Total Rows:** 11842

*   **disclosure_cycle**
    *   **Description:** The year of the CDP disclosure cycle.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   2024 Disclosure Cycle

*   **cdp_disclosing_org_number**
    *   **Description:** Unique identifier for the disclosing organization assigned by CDP.
    *   **Type:** Integer
    *   **Nulls:** 0 (0.0%)
    *   **Range:** 1093 to 2027923
    *   **Sample Values:**
        *   31146
        *   36039
        *   43970
        *   46263
        *   54408

*   **disclosing_organization**
    *   **Description:** Name of the organization (e.g., city, council) submitting the data.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Aberdeenshire Council
        *   Abington Township, PA
        *   Accra Metropolitan Assembly
        *   Addis Ababa City Administration
        *   Alcaldía de Cuenca
        *   Alcaldía de Villavicencio

*   **city_name**
    *   **Description:** Name of the city associated with the disclosure.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Aarhus
        *   Aberdeenshire
        *   Abington
        *   Accra
        *   Addis Ababa
        *   Ahmedabad

*   **country**
    *   **Description:** Country where the city is located.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Argentina
        *   Chile
        *   Colombia
        *   Costa Rica
        *   Denmark
        *   Ecuador

*   **currency_code**
    *   **Description:** Currency code for financial values (e.g., USD, EUR).
    *   **Type:** String
    *   **Nulls:** 48 (0.4%)
    *   **Sample Values:**
        *   CLP
        *   COP
        *   CRC
        *   DKK
        *   ETB
        *   GBP

*   **region**
    *   **Description:** Geographical region of the city.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Africa
        *   Eastern Asia
        *   Europe
        *   Latin America and the Caribbean
        *   Middle East
        *   North America

*   **record_type**
    *   **Description:** Indicates whether the row represents a 'project', 'goal', or 'action'.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   action
        *   goal
        *   project

*   **question_number**
    *   **Description:** The specific question number from the CDP questionnaire.
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Q5.1.1
        *   Q9.1
        *   Q9.3

*   **row_order**
    *   **Description:** The order of the row in the original questionnaire response.
    *   **Type:** Integer
    *   **Nulls:** 0 (0.0%)
    *   **Range:** 1 to 285
    *   **Sample Values:**
        *   1
        *   2
        *   3
        *   4
        *   5

*   **goal_base_year**
    *   **Description:** The base year against which the goal is measured.
    *   **Type:** Integer
    *   **Nulls:** 8267 (69.8%)
    *   **Range:** 1990 to 2027
    *   **Sample Values:**
        *   2015
        *   2018
        *   2020
        *   2021
        *   2022
        *   2023

*   **goal_comment**
    *   **Description:** Additional comments describing the goal.
    *   **Type:** String
    *   **Nulls:** 8965 (75.7%)
    *   **Sample Values:**
        *   It is a major priority for the City of Aarhus to further biodiversity...
        *   The trees will also contribute to solving significant challenges...
        *   This reduces impermeable areas while increasing...
        *   Aarhus has been working with this issue for many years...
        *   Over 400 informal waste workers were enrolled onto the NHIS...

*   **goal_hazards**
    *   **Description:** Climate hazards the goal aims to address (e.g., Flooding, Heat).
    *   **Type:** String
    *   **Nulls:** 8234 (69.5%)
    *   **Sample Values:**
        *   Biodiversity loss
        *   Heat stress, Extreme heat
        *   Storm, Urban flooding, Coastal flooding (incl. sea level rise)
        *   Urban flooding, Infectious disease
        *   Urban flooding, River flooding, Heavy precipitation

*   **goal_id**
    *   **Description:** Unique identifier for the goal within the disclosure.
    *   **Type:** String
    *   **Nulls:** 8230 (69.5%)
    *   **Sample Values:**
        *   Adaptation goal 1
        *   Adaptation goal 2
        *   Adaptation goal 3
        *   Adaptation goal 4
        *   Adaptation goal 5

*   **goal_metric_description**
    *   **Description:** Description of how the goal is measured.
    *   **Type:** String
    *   **Nulls:** 8396 (70.9%)
    *   **Sample Values:**
        *   Increase water storage in the range of 1-2 million m3.
        *   Number of transfer constructed and commissioned for use.
        *   The number of planted trees set to increase by 10,000 no later than 2025.
        *   The Township's Master Tree Action plan calls for increasing its tree canopy...
        *   This climate adaptation action is called for in the Township's Vision2035...

*   **goal_name**
    *   **Description:** Title or name of the adaptation goal.
    *   **Type:** String
    *   **Nulls:** 8230 (69.5%)
    *   **Sample Values:**
        *   10.000.000 trees
        *   Biodiversity
        *   Doubling water storage capacity in river valleys...
        *   Implement naturalized stormwater management features
        *   Increase awareness of the impacts of climate change...

*   **goal_target_year**
    *   **Description:** The target year for achieving the goal.
    *   **Type:** Integer
    *   **Nulls:** 8341 (70.4%)
    *   **Range:** 2016 to 2165
    *   **Sample Values:**
        *   2025
        *   2026
        *   2030
        *   2040
        *   2050

*   **action_cobenefits**
    *   **Description:** Additional benefits of the action beyond adaptation (e.g., Health, Economic).
    *   **Type:** String
    *   **Nulls:** 7447 (62.9%)
    *   **Sample Values:**
        *   Economic: Reduced costs
        *   Public Health: Improved air quality
        *   Public Health: Improved physical health, Public Health: Improved mental...
        *   Environmental: Increased/improved green space...
        *   Social: Reduced fuel/energy poverty...

*   **action_description**
    *   **Description:** Detailed description of the adaptation action.
    *   **Type:** String
    *   **Nulls:** 6405 (54.1%)
    *   **Sample Values:**
        *   The Paths Team are building more resilient, sustainable paths...
        *   Greenspace Officers and the Aberdeenshire Greenspace Officers...
        *   The Stonehaven Flood Protection Scheme has been protecting homes...
        *   The Bridges Service operates a bridge scour alert system...
        *   Accra is yet to attain universal waste collection coverage...

*   **action_ecosystem_impact_pct**
    *   **Description:** Estimated percentage of the ecosystem impacted by the action.
    *   **Type:** String
    *   **Nulls:** 7019 (59.3%)
    *   **Sample Values:**
        *   ≤10%
        *   11-20%
        *   21-30%
        *   31-40%
        *   41-50%

*   **action_funding_sources**
    *   **Description:** Sources of funding for the action.
    *   **Type:** String
    *   **Nulls:** 6902 (58.3%)
    *   **Sample Values:**
        *   Jurisdiction's own resources
        *   National funds and programmes
        *   International (including ODA)
        *   Public-private partnerships
        *   Regional funds and programmes

*   **action_hazards**
    *   **Description:** Climate hazards the action aims to mitigate or adapt to.
    *   **Type:** String
    *   **Nulls:** 6437 (54.4%)
    *   **Sample Values:**
        *   Biodiversity loss, Drought
        *   Fire weather (risk of wildfires), Mass movement, River flooding
        *   Storm, Urban flooding, Coastal flooding (incl. sea level rise)
        *   Urban flooding
        *   Urban flooding, Infectious disease

*   **action_id**
    *   **Description:** Unique identifier for the action within the disclosure.
    *   **Type:** String
    *   **Nulls:** 7365 (62.2%)
    *   **Sample Values:**
        *   Adaptation Action 1
        *   Adaptation Action 2
        *   Adaptation Action 3
        *   Adaptation Action 4
        *   Adaptation Action 5

*   **action_in_climate_plan**
    *   **Description:** Indicates if the action is part of a formal climate plan.
    *   **Type:** String
    *   **Nulls:** 6874 (58.0%)
    *   **Sample Values:**
        *   Action is included in climate action plan and/or development/master plan
        *   Action is not included in climate action plan and/or development/master plan
        *   No climate action plan and/or development/master plan has been developed
        *   Other: The action is an urban planning toolkit
        *   Other: Es un producto planteado en la Poítica Pública de Acción Climática

*   **action_name**
    *   **Description:** Name or category of the adaptation action.
    *   **Type:** String
    *   **Nulls:** 6347 (53.6%)
    *   **Sample Values:**
        *   Ecosystem-based actions: Ecological corridors
        *   Ecosystem-based actions: Afforestation and reforestation
        *   Engineered and built environment actions: Building codes
        *   Engineered and built environment actions: Flood defence...
        *   Government policies and programs actions: Adaptive management

*   **action_population_impact_pct**
    *   **Description:** Estimated percentage of the population impacted by the action.
    *   **Type:** String
    *   **Nulls:** 6738 (56.9%)
    *   **Sample Values:**
        *   ≤10%
        *   11-20%
        *   21-30%
        *   31-40%
        *   81-90%

*   **action_resilience_attributes**
    *   **Description:** Attributes contributing to resilience (e.g., Community participation).
    *   **Type:** String
    *   **Nulls:** 7423 (62.7%)
    *   **Sample Values:**
        *   Anticipation & preparedness
        *   Planning & strategy
        *   Natural resources, Community participation
        *   Anticipation & preparedness, Infrastructural assets
        *   Planning & strategy, Decision-making capacity...

*   **action_sectors**
    *   **Description:** Sectors affected by or involved in the action.
    *   **Type:** String
    *   **Nulls:** 6519 (55.0%)
    *   **Sample Values:**
        *   Agriculture
        *   Water supply, Forestry
        *   Waste management, Human health and social work activities
        *   Sewerage, wastewater management and remediation activities...
        *   Real estate activities

*   **action_status**
    *   **Description:** Current implementation status of the action.
    *   **Type:** String
    *   **Nulls:** 7049 (59.5%)
    *   **Sample Values:**
        *   Action in operation (jurisdiction-wide)
        *   Action in operation (targeted to sector/location)
        *   Implementation complete in the reporting year
        *   Implementation underway with completion expected in less than one year
        *   Scoping

*   **action_timeframe**
    *   **Description:** Expected timeframe for the action.
    *   **Type:** String
    *   **Nulls:** 6593 (55.7%)
    *   **Sample Values:**
        *   Short-term (by 2025)
        *   Medium-term (2026-2050)
        *   Long-term (after 2050)
        *   Do not know
        *   Not known (not possible to define)

*   **action_total_cost**
    *   **Description:** Total cost of the action in the reported currency.
    *   **Type:** Float
    *   **Nulls:** 8801 (74.3%)
    *   **Range:** 0 to 22,900,000,000,000
    *   **Sample Values:**
        *   0.0
        *   175,430.0
        *   300,000.0
        *   3,000,000.0
        *   15,000,000.0

*   **action_total_cost_usd**
    *   **Description:** Total cost of the action converted to USD.
    *   **Type:** Float
    *   **Nulls:** 8816 (74.4%)
    *   **Range:** 0 to 16,259,000,000
    *   **Sample Values:**
        *   0.0
        *   20,100.0
        *   115,000.0
        *   175,430.0
        *   3,150,000.0

*   **project_area**
    *   **Description:** The specific area or domain the project focuses on.
    *   **Type:** String
    *   **Nulls:** 9203 (77.7%)
    *   **Sample Values:**
        *   Buildings
        *   Transport
        *   Renewable energy
        *   Water management
        *   Public and green spaces

*   **project_description**
    *   **Description:** Detailed description of the project.
    *   **Type:** String
    *   **Nulls:** 9503 (80.2%)
    *   **Sample Values:**
        *   Se busca optimizar y ampliar el sistema de tratamiento...
        *   The bidding request and description for this project may be found...
        *   As Accra prepares for implementation of city wide source separation...
        *   Development of large scale compost plant with capacity of approximately...
        *   Reducir el riesgo de desabastecimiento del recurso hídrico...

*   **project_financing_model**
    *   **Description:** The model used to finance the project.
    *   **Type:** String
    *   **Nulls:** 9525 (80.4%)
    *   **Sample Values:**
        *   Grants
        *   Public finance- own budget
        *   Public finance- national government
        *   Public-private partnership
        *   Loans from commercial banks

*   **project_financing_status**
    *   **Description:** Status of securing funding for the project.
    *   **Type:** String
    *   **Nulls:** 9371 (79.1%)
    *   **Sample Values:**
        *   Project not funded and seeking full funding
        *   Project not funded and seeking partial funding
        *   Project partially funded and seeking additional funding
        *   Feasibility studies and preparation of finance ready project in progress
        *   Other: Funded

*   **project_investment_needed**
    *   **Description:** Investment required for the project in reported currency.
    *   **Type:** Float
    *   **Nulls:** 10204 (86.2%)
    *   **Range:** 0 to 2,800,000,000,000,000
    *   **Sample Values:**
        *   42,500.0
        *   581,481.0
        *   2,500,000.0
        *   10,500,000.0
        *   89,220,000.0

*   **project_investment_needed_usd**
    *   **Description:** Investment required for the project in USD.
    *   **Type:** Float
    *   **Nulls:** 10210 (86.2%)
    *   **Range:** 0 to 3,556,000,000,000,000
    *   **Sample Values:**
        *   5,000.0
        *   21,000.0
        *   42,500.0
        *   82,303.2
        *   161,000.0

*   **project_linked_action_id**
    *   **Description:** ID of an action linked to this project (if any).
    *   **Type:** String
    *   **Nulls:** 10656 (90.0%)
    *   **Sample Values:**
        *   No linked action
        *   Adaptation Action 1
        *   Adaptation Action 5
        *   Mitigation Action 1
        *   Mitigation Action 2

*   **project_stage**
    *   **Description:** Current stage of the project lifecycle.
    *   **Type:** String
    *   **Nulls:** 9360 (79.0%)
    *   **Sample Values:**
        *   Implementation
        *   Project feasibility
        *   Project structuring
        *   Scoping
        *   Transaction preparation

*   **project_title**
    *   **Description:** Title of the project.
    *   **Type:** String
    *   **Nulls:** 9373 (79.2%)
    *   **Sample Values:**
        *   Acueducto Fallas
        *   Paisajes del Agua
        *   Modernización del acueducto de la Garita
        *   Inclusive Transport Transformation in Accra
        *   The Aarhus 2030 Mission Plan...

*   **project_total_cost**
    *   **Description:** Total cost of the project in reported currency.
    *   **Type:** Float
    *   **Nulls:** 9836 (83.1%)
    *   **Range:** 0 to 2,800,000,000,000,000
    *   **Sample Values:**
        *   85,000.0
        *   581,481.0
        *   2,500,000.0
        *   10,500,000.0
        *   89,220,000.0

*   **project_total_cost_usd**
    *   **Description:** Total cost of the project in USD.
    *   **Type:** Float
    *   **Nulls:** 9842 (83.1%)
    *   **Range:** 0 to 3,556,000,000,000,000
    *   **Sample Values:**
        *   5,000.0
        *   21,000.0
        *   82,303.2
        *   85,000.0
        *   161,000.0

*   **Stage**
    *   **Description:** Categorization of the row (Goal, Action, Project).
    *   **Type:** String
    *   **Nulls:** 0 (0.0%)
    *   **Sample Values:**
        *   Action Complete
        *   Action Implementation
        *   Goal
        *   Project Complete
        *   Project Planning - Seeking Funding

*   **goal_name_en**
    *   **Description:** English translation of `goal_name`.
    *   **Type:** String
    *   **Nulls:** 8230 (69.5%)
    *   **Sample Values:**
        *   10,000,000 trees
        *   Biodiversity
        *   Implement naturalized stormwater management features
        *   Improve the quality of citizens working in the informalsector...
        *   Understand the impacts of climate change on infrastructure...

*   **goal_comment_en**
    *   **Description:** English translation of `goal_comment`.
    *   **Type:** String
    *   **Nulls:** 9038 (76.3%)
    *   **Sample Values:**
        *   This reduces impermeable areas while increasing...
        *   The city developed a resilient strategy through 100 Resilient Cities...
        *   It is a major priority for the City of Aarhus to further biodiversity...
        *   The trees will also contribute to solving significant challenges...
        *   Availability of transfer with access to informal waste collectors...

*   **goal_metric_description_en**
    *   **Description:** English translation of `goal_metric_description`.
    *   **Type:** String
    *   **Nulls:** 8405 (71.0%)
    *   **Sample Values:**
        *   Increase water storage in the range of 1-2 million m3.
        *   Number of transfer constructed and commissioned for use.
        *   The number of planted trees set to increase by 10,000 no later than 2025.
        *   The Township's Master Tree Action plan calls for increasing its tree canopy...
        *   This climate adaptation action is called for in the Township's Vision2035...

*   **action_name_en**
    *   **Description:** English translation of `action_name`.
    *   **Type:** String
    *   **Nulls:** 6347 (53.6%)
    *   **Sample Values:**
        *   Ecosystem-based actions: Ecological corridors
        *   Engineered and built environment actions: Building codes
        *   Services actions: Ensure all waste generated is collected
        *   Government policies and programs actions: Adaptive management
        *   Educational/Informational actions: Community engagement/education

*   **action_description_en**
    *   **Description:** English translation of `action_description`.
    *   **Type:** String
    *   **Nulls:** 6405 (54.1%)
    *   **Sample Values:**
        *   Action plans are intended to be developed for Communities most vulnerable...
        *   Reforestation actions have been carried out in areas protecting water bodies...
        *   The Paths Team are building more resilient, sustainable paths...
        *   Accra is yet to attain universal waste collection coverage...
        *   The Stonehaven Flood Protection Scheme has been protecting homes...

*   **action_cobenefits_en**
    *   **Description:** English translation of `action_cobenefits`.
    *   **Type:** String
    *   **Nulls:** 7447 (62.9%)
    *   **Sample Values:**
        *   Economic: Reduced costs
        *   Public Health: Improved air quality
        *   Environmental: Improved water/soil quality...
        *   Social: Reduced fuel/energy poverty...
        *   Economic: Reduced disruption of energy, transport, water...

*   **action_hazards_en**
    *   **Description:** English translation of `action_hazards`.
    *   **Type:** String
    *   **Nulls:** 6437 (54.4%)
    *   **Sample Values:**
        *   Urban flooding
        *   Infectious disease
        *   Biodiversity loss, Drought
        *   Storm, Urban flooding, Coastal flooding (incl. sea level rise)
        *   Fire weather (risk of wildfires), Mass movement, River flooding

*   **project_title_en**
    *   **Description:** English translation of `project_title`.
    *   **Type:** String
    *   **Nulls:** 9374 (79.2%)
    *   **Sample Values:**
        *   Fallas Aqueduct
        *   Water Landscapes
        *   Wastewater treatment plant
        *   Inclusive Transport Transformation in Accra
        *   The Aarhus 2030 Mission Plan...

*   **project_description_en**
    *   **Description:** English translation of `project_description`.
    *   **Type:** String
    *   **Nulls:** 9504 (80.3%)
    *   **Sample Values:**
        *   Expand air quality monitoring stations...
        *   Seek to optimize and expand the wastewater treatment system...
        *   Project that includes land purchase, installation of tanks...
        *   Reduce the risk of water resource shortage in the urban area...
        *   As Accra prepares for implementation of city wide source separation...

*   **project_area_en**
    *   **Description:** English translation of `project_area`.
    *   **Type:** String
    *   **Nulls:** 9203 (77.7%)
    *   **Sample Values:**
        *   Buildings
        *   Transport
        *   Renewable energy
        *   Water management
        *   Public and green spaces

### Notes
*   **High Null Counts**: Columns specific to goals, actions, or projects will naturally have high null counts because each row typically represents only one of these types (indicated by `record_type`).
*   **Financial Values**: Extremely large values in cost columns might be due to currency conversion issues or data entry errors in the source.
*   **English Translations**: Columns ending in `_en` appear to be English translations or copies of the original text fields.