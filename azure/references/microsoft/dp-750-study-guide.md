# Study Guide for Exam DP-750: Implementing Data Engineering Solutions Using Azure Databricks

Source: https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-750
Retrieved: 2026-11-23

## Purpose of this document

This study guide should help you understand what to expect on the exam and includes a summary of the topics the exam might cover and links to additional resources. The information and materials in this document should help you focus your studies as you prepare for the exam.

| Useful links | Description |
|---|---|
| How to earn the certification | Some certifications only require passing one exam, while others require passing multiple exams. |
| [Certification renewal](https://learn.microsoft.com/en-us/credentials/certifications/renew-your-microsoft-certification) | Microsoft associate, expert, and specialty certifications expire annually. You can renew by passing a **free** online assessment on Microsoft Learn. |
| [Your Microsoft Learn profile](https://learn.microsoft.com/en-us/users) | Connecting your certification profile to Microsoft Learn allows you to schedule and renew exams and share and print certificates. |
| [Exam scoring and score reports](https://learn.microsoft.com/en-us/credentials/certifications/exam-scoring-reports) | A score of 700 or greater is required to pass. |
| [Exam sandbox](https://aka.ms/examdemo) | You can explore the exam environment by visiting our exam sandbox. |
| [Request accommodations](https://learn.microsoft.com/en-us/credentials/certifications/request-accommodations) | If you use assistive devices, require extra time, or need modification to any part of the exam experience, you can request an accommodation. |

## About the exam

### Languages

Some exams are localized into other languages, and those are updated approximately eight weeks after the English version is updated. If the exam isn't available in your preferred language, you can request an additional 30 minutes to complete the exam.

The bullets that follow each of the skills measured are intended to illustrate how we are assessing that skill. Related topics may be covered in the exam.

Most questions cover features that are general availability (GA). The exam may contain questions on Preview features if those features are commonly used.

## Skills measured as of March 11, 2026

### Audience profile

As a candidate for this Microsoft Certification, you should have subject matter expertise in integrating and modeling data, building and deploying optimized pipelines, and troubleshooting and maintaining workloads in Azure Databricks. You should also have experience applying data quality and data governance best practices in Unity Catalog.

You need to know how to ingest and transform data by using Structured Query Language (SQL) and Python. You need experience with software development lifecycle (SDLC) practices, including Git. Additionally, you should be familiar with Microsoft Entra, Azure Data Factory, and Azure Monitor.

Your responsibilities for this role include:

- Setting up and configuring an Azure Databricks environment.
- Securing and governing Unity Catalog objects.
- Preparing and processing data.
- Deploying and maintaining data pipelines and workloads.

You work closely with administrators, platform architects, solution architects, data scientists, and data analysts to design, deploy, and secure data engineering solutions by using Azure Databricks.

### Skills at a glance

- Set up and configure an Azure Databricks environment (15–20%)
- Secure and govern Unity Catalog objects (15–20%)
- Prepare and process data (30–35%)
- Deploy and maintain data pipelines and workloads (30–35%)

### Set up and configure an Azure Databricks environment (15–20%)

#### Select and configure compute in a workspace

- Choose an appropriate compute type, including job compute, serverless, warehouse, classic compute, and shared compute
- Configure compute performance settings, including CPU, node count, autoscaling, termination, node type, cluster size, and pooling
- Configure compute feature settings, including Photon acceleration, Azure Databricks runtime/Spark version, and machine learning
- Install libraries for a compute resource
- Configure access permissions to a compute resource

#### Create and organize objects in Unity Catalog

- Apply naming conventions based on requirements, including isolation, development environment, and external sharing
- Create a catalog based on requirements
- Create a schema based on requirements
- Create volumes based on requirements
- Create tables, views, and materialized views
- Implement a foreign catalog by configuring connections
- Implement data definition language (DDL) operations on managed and external tables
- Configure AI/BI Genie instructions for data discovery

### Secure and govern Unity Catalog objects (15–20%)

#### Secure Unity Catalog objects

- Grant privileges to a principal (user, service principal, or group) for securable objects in Unity Catalog
- Implement table- and column-level access control and row-level security
- Access Azure Key Vault secrets from within Azure Databricks
- Authenticate data access by using service principals
- Authenticate resource access by using managed identities

#### Govern Unity Catalog objects

- Create, implement, and preserve table and column definitions and descriptions for data discovery
- Configure attribute-based access control (ABAC) by using tags and policies
- Configure row filters and column masks
- Apply data retention policies
- Set up and manage data lineage tracking by using Catalog Explorer, including owner, history, dependencies, and lineage
- Configure audit logging
- Design and implement a secure strategy for Delta Sharing

### Prepare and process data (30–35%)

#### Design and implement data modeling in Unity Catalog

- Design logic for data ingestion and data source configuration, including extraction type and file type
- Choose an appropriate data ingestion tool, including Lakeflow Connect, notebooks, and Azure Data Factory
- Choose a data loading method, including batch and streaming
- Choose a data table format, such as Parquet, Delta, CSV, JSON, or Iceberg
- Design and implement a data partitioning scheme
- Choose a slowly changing dimension (SCD) type
- Choose granularity on a column or table based on requirements
- Design and implement a temporal (history) table to record changes over time
- Design and implement a clustering strategy, including liquid clustering, Z-ordering, and deletion vectors
- Choose between managed and unmanaged tables

#### Ingest data into Unity Catalog

- Ingest data by using Lakeflow Connect, including batch and streaming
- Ingest data by using notebooks, including batch and streaming
- Ingest data by using SQL methods, including CREATE TABLE … AS (CTAS), CREATE OR REPLACE TABLE, and COPY INTO
- Ingest data by using a change data capture (CDC) feed
- Ingest data by using Spark Structured Streaming
- Ingest streaming data from Azure Event Hubs
- Ingest data by using Lakeflow Spark Declarative Pipelines, including Auto Loader

#### Cleanse, transform, and load data into Unity Catalog

- Profile data to generate summary statistics and assess data distributions
- Choose appropriate column data types
- Identify and resolve duplicate, missing, and null values
- Transform data, including filtering, grouping, and aggregating data
- Transform data by using join, union, intersect, and except operators
- Transform data by denormalizing, pivoting, and unpivoting data
- Load data by using merge, insert, and append operations

#### Implement and manage data quality constraints in Unity Catalog

- Implement validation checks, including nullability, data cardinality, and range checking
- Implement data type checks
- Implement schema enforcement and manage schema drift
- Manage data quality with pipeline expectations in Lakeflow Spark Declarative Pipelines

### Deploy and maintain data pipelines and workloads (30–35%)

#### Design and implement data pipelines

- Design order of operations for a data pipeline
- Choose between notebook and Lakeflow Spark Declarative Pipelines
- Design task logic for Lakeflow Jobs
- Design and implement error handling in data pipelines, notebooks, and jobs
- Create a data pipeline by using a notebook, including precedence constraints
- Create a data pipeline by using Lakeflow Spark Declarative Pipelines

#### Implement Lakeflow Jobs

- Create a job, including setup and configuration
- Configure job triggers
- Schedule a job
- Configure alerts for a job
- Configure automatic restarts for a job or a data pipeline

#### Implement development lifecycle processes in Azure Databricks

- Apply version control best practices using Git
- Manage branching, pull requests, and conflict resolution
- Implement a testing strategy, including unit tests, integration tests, end-to-end tests, and user acceptance testing (UAT)
- Configure and package Databricks Asset Bundles
- Deploy a bundle by using the Azure Databricks command-line interface (CLI)
- Deploy a bundle by using REST APIs

#### Monitor, troubleshoot, and optimize workloads in Azure Databricks

- Monitor and manage cluster consumption to optimize performance and cost
- Troubleshoot and repair issues in Lakeflow Jobs, including repair, restart, stop, and run functions
- Troubleshoot and repair issues in Apache Spark jobs and notebooks, including performance tuning, resolving resource bottlenecks, and cluster restart
- Investigate and resolve caching, skewing, spilling, and shuffle issues by using a Directed Acyclic Graph (DAG), the Spark UI, and query profile
- Optimize Delta tables for performance and cost, including OPTIMIZE and VACUUM commands
- Implement log streaming by using Log Analytics in Azure Monitor
- Configure alerts by using Azure Monitor

## Study resources

We recommend that you train and get hands-on experience before you take the exam. We offer self-study options and classroom training as well as links to documentation, community sites, and videos.

| Study resources | Links to learning and documentation |
|---|---|
| Get trained | [Choose from self-paced learning paths and modules or take an instructor-led course](https://learn.microsoft.com/en-us/credentials/certifications/exams/dp-750#two-ways-to-prepare) |
| Find documentation | [Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/)[Azure Data Factory](https://learn.microsoft.com/en-us/azure/data-factory/introduction)[Microsoft Entra](https://learn.microsoft.com/en-us/entra/)[Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/overview) |
| Ask a question | [Microsoft Q&A \| Microsoft Docs](https://learn.microsoft.com/en-us/answers/products/) |
| Get community support | [Analytics on Azure - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/analytics-on-azure/bd-p/AnalyticsonAzureDiscussion)[Azure Databricks - Community Hub](https://techcommunity.microsoft.com/category/azure/blog/azure-databricks) |
| Follow Microsoft Learn | [Microsoft Learn - Microsoft Tech Community](https://techcommunity.microsoft.com/t5/microsoft-learn/ct-p/MicrosoftLearn) |
| Find a video | [Exam Readiness Zone](https://learn.microsoft.com/en-us/shows/exam-readiness-zone/)[Data Exposed](https://learn.microsoft.com/en-us/shows/data-exposed/)[Browse other Microsoft Learn shows](https://learn.microsoft.com/en-us/shows/browse) |
