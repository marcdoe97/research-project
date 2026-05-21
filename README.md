# Guided Requirements Artefact

This is a deployable PHP/SQLite web application for a requirements engineering study.

The application does not call an AI API and does not require Ollama or any server-side AI installation. Instead, participants first write their own requirements for the study scenario. The application then combines those participant-written requirements with the same standardized system prompt for every participant. Participants paste that generated prompt into ChatGPT and paste the complete ChatGPT response back into the application. The application stores and evaluates the result locally.

## Study Use Case

All participants work with the same scenario:

```text
University exam registration system

Students should be able to register for exams online. Registration should only work
during the official registration period. Students should not be able to register if they
have not fulfilled the course prerequisites. After registering, they should get a
confirmation somehow. The system should also prevent duplicate registrations.
Admins need to be able to see who registered.
```

## Features

- password-protected study interface
- standardized guided ChatGPT workflow based on participant-written requirements
- manual control group workflow without AI support
- EARS template conformance checks
- requirements smell detection
- traceability overview
- evaluation dashboard
- CSV exports for requirements, quality reports, test cases, and logs

## Password Protection

Participant input pages are protected with the participation password:

```text
Research_Project
```

Evaluation-related pages are protected with a separate evaluation password:

- History
- Traceability
- Evaluation
- Logs
- CSV exports

Evaluation password:

```text
Auswertung
```

## Deployment

Upload the full `research_project` folder to a PHP-capable web server.

Required PHP extension:

- `pdo_sqlite`

The application creates its SQLite database in:

```text
data/research.sqlite
```

Operational logs are written to:

```text
logs/evaluation.log
```

The included `.htaccess` files block direct browser access to `data/` and `logs/` on Apache-compatible hosting.

## Evaluation Workflow

1. Use **Guided ChatGPT** for participants in the tool-supported group.
2. The participant writes initial requirements for the scenario.
3. The application generates a prompt from the fixed system prompt and the participant's own requirements.
4. The participant copies that prompt into ChatGPT without changing it.
5. The participant pastes the full ChatGPT response back into the application.
6. Use **Control Group** for participants working manually without AI support.
7. Enter the manual effort in seconds for both groups.
8. Use **Evaluation** to compare conformance, smell count, traceability, and effort.
9. Export CSV files from **Evaluation**, **History**, or **Logs** for external analysis.
