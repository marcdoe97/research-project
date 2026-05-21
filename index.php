<?php
declare(strict_types=1);

/*
 * Guided ChatGPT Requirements Engineering Artefact
 * Deployable PHP/SQLite web application for the DSR evaluation study.
 */

session_start();
date_default_timezone_set('Europe/Berlin');

const APP_NAME = 'Guided Requirements Artefact';
const PARTICIPATION_PASSWORD = 'Research_Project';
const EVALUATION_PASSWORD = 'Auswertung';
const DB_PATH = __DIR__ . '/data/research.sqlite';
const LOG_PATH = __DIR__ . '/logs/evaluation.log';
const STUDY_CASE = "University exam registration system\n\nStudents should be able to register for exams online. Registration should only work\nduring the official registration period. Students should not be able to register if they\nhave not fulfilled the course prerequisites. After registering, they should get a\nconfirmation somehow. The system should also prevent duplicate registrations.\nAdmins need to be able to see who registered.";

if (is_file(__DIR__ . '/config.local.php')) {
    require __DIR__ . '/config.local.php';
}

ensureRuntime();
$db = db();
initDb($db);

if (isset($_GET['logout'])) {
    $area = $_GET['logout'];
    if ($area === 'evaluation') {
        unset($_SESSION['evaluation_authenticated']);
        header('Location: index.php?page=dashboard');
        exit;
    }
    if ($area === 'participation') {
        unset($_SESSION['participation_authenticated']);
        header('Location: index.php');
        exit;
    }
    $_SESSION = [];
    session_destroy();
    header('Location: index.php');
    exit;
}

$page = $_GET['page'] ?? 'tool';
$notice = null;
$error = null;
$result = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $action = $_POST['action'] ?? '';
        if ($action === 'login') {
            $area = (string)($_POST['area'] ?? 'participation');
            $password = (string)($_POST['password'] ?? '');
            if ($area === 'evaluation' && hash_equals(EVALUATION_PASSWORD, $password)) {
                $_SESSION['evaluation_authenticated'] = true;
                logEvent($db, 'info', 'Evaluation login succeeded');
                header('Location: index.php?page=dashboard');
                exit;
            }
            if ($area === 'participation' && hash_equals(PARTICIPATION_PASSWORD, $password)) {
                $_SESSION['participation_authenticated'] = true;
                logEvent($db, 'info', 'Participation login succeeded');
                header('Location: index.php');
                exit;
            }
            $error = 'Invalid password.';
        } elseif ($action === 'save_tool') {
            $result = handleToolRun($db);
            $notice = 'Tool-supported requirement saved as ' . $result['req_id'] . '.';
            $page = 'tool';
        } elseif ($action === 'save_control') {
            $result = handleControlRun($db);
            $notice = 'Control group requirement saved as ' . $result['req_id'] . '.';
            $page = 'control';
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
        logEvent($db, 'error', 'Request failed: ' . $error);
    }
}

if (isset($_GET['export'])) {
    if (!isEvaluationAuthenticated()) {
        renderLogin('evaluation', 'Please log in to export evaluation data.');
        exit;
    }
    exportCsv($db, $_GET['export']);
}

if (isEvaluationPage($page) && !isEvaluationAuthenticated()) {
    renderLogin('evaluation', $error ?: 'Please log in to view evaluation data.');
    exit;
}

if (!isEvaluationPage($page) && !isParticipationAuthenticated()) {
    renderLogin('participation', $error ?: 'Please log in to participate in the study.');
    exit;
}

renderPage($db, $page, $notice, $error, $result);

function ensureRuntime(): void
{
    foreach ([__DIR__ . '/data', __DIR__ . '/logs'] as $dir) {
        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
        }
    }
    if (!is_file(LOG_PATH)) {
        file_put_contents(LOG_PATH, '');
    }
}

function db(): PDO
{
    $pdo = new PDO('sqlite:' . DB_PATH);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec('PRAGMA foreign_keys = ON');
    return $pdo;
}

function initDb(PDO $db): void
{
    $db->exec("
        CREATE TABLE IF NOT EXISTS requirements (
            req_id TEXT PRIMARY KEY,
            group_name TEXT NOT NULL DEFAULT 'tool',
            participant_id TEXT,
            raw_input TEXT NOT NULL,
            structured_req TEXT,
            source_prompt TEXT,
            ai_response TEXT,
            effort_seconds INTEGER DEFAULT 0,
            llm_duration_seconds REAL DEFAULT 0,
            quality_duration_seconds REAL DEFAULT 0,
            test_duration_seconds REAL DEFAULT 0,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS quality_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            req_id TEXT NOT NULL,
            smell_count INTEGER DEFAULT 0,
            conformance INTEGER DEFAULT 0,
            conformance_notes TEXT,
            smells_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (req_id) REFERENCES requirements(req_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS test_cases (
            tc_id TEXT PRIMARY KEY,
            req_id TEXT NOT NULL,
            raw_output TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (req_id) REFERENCES requirements(req_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS event_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            context_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ");
    foreach ([
        "ALTER TABLE requirements ADD COLUMN source_prompt TEXT",
        "ALTER TABLE requirements ADD COLUMN ai_response TEXT",
    ] as $migration) {
        try {
            $db->exec($migration);
        } catch (Throwable $e) {
            // Column already exists on upgraded installations.
        }
    }
}

function handleToolRun(PDO $db): array
{
    $raw = trim((string)($_POST['raw_input'] ?? ''));
    $aiResponse = trim((string)($_POST['ai_response'] ?? ''));
    if ($raw === '') {
        throw new RuntimeException('Enter your drafted requirements before saving the guided result.');
    }
    if ($aiResponse === '') {
        throw new RuntimeException('Paste the ChatGPT response before saving the tool-supported result.');
    }

    $participant = cleanId((string)($_POST['participant_id'] ?? ''));
    $effort = max(0, (int)($_POST['effort_seconds'] ?? 0));
    $reqId = nextRequirementId($db, 'REQ');
    $tcIds = [];
    for ($i = 0; $i < 5; $i++) {
        $tcIds[] = nextTestCaseId($db, $i);
    }
    $prompt = chatGptPrompt($raw);
    $structured = extractStructuredRequirement($aiResponse);
    $tests = extractTestCases($aiResponse);
    $smells = detectSmells($structured);
    [$conformance, $notes] = checkConformance($structured);
    $quality = [
        'smells' => $smells,
        'smell_count' => count($smells),
        'conformance' => $conformance,
        'conformance_notes' => $notes ?: 'Structured output pasted from the guided ChatGPT workflow.',
    ];

    saveRequirement($db, [
        'req_id' => $reqId,
        'group_name' => 'tool',
        'participant_id' => $participant,
        'raw_input' => $raw,
        'structured_req' => $structured,
        'source_prompt' => $prompt,
        'ai_response' => $aiResponse,
        'effort_seconds' => $effort,
        'llm_duration_seconds' => 0,
        'quality_duration_seconds' => 0,
        'test_duration_seconds' => 0,
        'error_message' => null,
    ]);
    saveQuality($db, $reqId, $quality);
    saveTestCases($db, $reqId, $tcIds, $tests);

    logEvent($db, 'info', "Guided ChatGPT result saved for {$reqId}", [
        'participant_id' => $participant,
        'effort_seconds' => $effort,
        'smell_count' => $quality['smell_count'],
        'conformance' => $quality['conformance'],
    ]);

    return [
        'req_id' => $reqId,
        'structured_req' => $structured,
        'quality' => $quality,
        'test_cases' => $tests,
        'tc_ids' => $tcIds,
        'duration' => $effort,
    ];
}

function handleControlRun(PDO $db): array
{
    $raw = trim((string)($_POST['raw_input'] ?? ''));
    if ($raw === '') {
        throw new RuntimeException('Enter the manually written requirement before saving it.');
    }

    $participant = cleanId((string)($_POST['participant_id'] ?? ''));
    $effort = max(0, (int)($_POST['effort_seconds'] ?? 0));
    $reqId = nextRequirementId($db, 'CTRL');
    $smells = detectSmells($raw);
    [$conformance, $notes] = checkConformance($raw);
    $quality = [
        'smells' => $smells,
        'smell_count' => count($smells),
        'conformance' => $conformance,
        'conformance_notes' => $notes ?: 'Manual baseline entry.',
    ];

    saveRequirement($db, [
        'req_id' => $reqId,
        'group_name' => 'control',
        'participant_id' => $participant,
        'raw_input' => $raw,
        'structured_req' => '',
        'source_prompt' => '',
        'ai_response' => '',
        'effort_seconds' => $effort,
        'llm_duration_seconds' => 0,
        'quality_duration_seconds' => 0,
        'test_duration_seconds' => 0,
        'error_message' => null,
    ]);
    saveQuality($db, $reqId, $quality);
    logEvent($db, 'info', "Control group entry saved for {$reqId}", [
        'smell_count' => $quality['smell_count'],
        'conformance' => $quality['conformance'],
    ]);

    return ['req_id' => $reqId, 'quality' => $quality];
}

function standardizedSystemPrompt(): string
{
    return <<<PROMPT
You are supporting a requirements engineering study as a requirements engineering assistant.

Follow these rules strictly:
- Use English only.
- Do not ask clarifying questions.
- Do not explain your reasoning.
- Use only the requirements provided by the participant.
- Do not invent additional business rules, actors, constraints, dates, thresholds, or system functions.
- If information is missing, use [PLACEHOLDER] instead of making assumptions.
- Improve the participant's requirements by making them clear, testable, and EARS-style.
- Create acceptance test cases that are directly traceable to the improved requirements.
- Replace vague terms with measurable or verifiable wording only when the participant provided enough information.

Output format:

STRUCTURED_REQUIREMENTS
REQ-1:
WHEN <trigger condition>
THE SYSTEM SHALL <observable system behavior>

REQ-2:
WHEN <trigger condition>
THE SYSTEM SHALL <observable system behavior>

REQ-3:
WHEN <trigger condition>
THE SYSTEM SHALL <observable system behavior>

REQ-4:
WHEN <trigger condition>
THE SYSTEM SHALL <observable system behavior>

REQ-5:
WHEN <trigger condition>
THE SYSTEM SHALL <observable system behavior>

ACCEPTANCE_TEST_CASES
TC-1:
LINKED_REQUIREMENT: REQ-1
PRECONDITIONS: <preconditions>
STEPS:
1. <action>
2. <action>
EXPECTED_RESULT: <observable result>

TC-2:
LINKED_REQUIREMENT: REQ-2
PRECONDITIONS: <preconditions>
STEPS:
1. <action>
2. <action>
EXPECTED_RESULT: <observable result>

TC-3:
LINKED_REQUIREMENT: REQ-3
PRECONDITIONS: <preconditions>
STEPS:
1. <action>
2. <action>
EXPECTED_RESULT: <observable result>

TC-4:
LINKED_REQUIREMENT: REQ-4
PRECONDITIONS: <preconditions>
STEPS:
1. <action>
2. <action>
EXPECTED_RESULT: <observable result>

TC-5:
LINKED_REQUIREMENT: REQ-5
PRECONDITIONS: <preconditions>
STEPS:
1. <action>
2. <action>
EXPECTED_RESULT: <observable result>

SELF_CHECK
Template conformance: <Pass or Fail>
Ambiguities resolved: <short statement>
Missing information placeholders: <list or None>
PROMPT;
}

function chatGptPrompt(string $participantRequirements): string
{
    return standardizedSystemPrompt() . <<<PROMPT


Participant requirements:
"""{$participantRequirements}"""
PROMPT;
}

function extractStructuredRequirement(string $response): string
{
    $structured = extractSection($response, 'STRUCTURED_REQUIREMENTS', 'ACCEPTANCE_TEST_CASES');
    return $structured !== '' ? $structured : $response;
}

function extractTestCases(string $response): string
{
    $tests = extractSection($response, 'ACCEPTANCE_TEST_CASES', 'SELF_CHECK');
    return $tests !== '' ? $tests : $response;
}

function extractSection(string $text, string $start, string $end): string
{
    $pattern = '/' . preg_quote($start, '/') . '\s*(.*?)\s*' . preg_quote($end, '/') . '/is';
    if (preg_match($pattern, $text, $matches)) {
        return trim($matches[1]);
    }
    return '';
}

function detectSmells(string $text): array
{
    $patterns = [
        '/\bshould\b/i' => "Ambiguity: 'should' implies optionality; use 'shall'.",
        '/\bmight\b/i' => "Ambiguity: 'might' is non-committal.",
        '/\bmaybe\b/i' => "Ambiguity: 'maybe' is non-committal.",
        '/\bpossibly\b/i' => "Ambiguity: 'possibly' is non-committal.",
        '/\busually\b/i' => "Ambiguity: 'usually' is context-dependent.",
        '/\boften\b/i' => "Ambiguity: 'often' lacks a measurable threshold.",
        '/\bsometimes\b/i' => "Ambiguity: 'sometimes' lacks a measurable threshold.",
        '/\bappropriate\b/i' => "Vagueness: 'appropriate' is not measurable.",
        '/\badequate\b/i' => "Vagueness: 'adequate' is not measurable.",
        '/\bsufficient\b/i' => "Vagueness: 'sufficient' is not measurable.",
        '/\betc\.?\b/i' => "Incompleteness: 'etc.' leaves scope undefined.",
        '/\band\/or\b/i' => "Ambiguity: 'and/or' creates ambiguous logic.",
        '/\bmany\b/i' => "Vagueness: 'many' has no measurable threshold.",
        '/\bfew\b/i' => "Vagueness: 'few' has no measurable threshold.",
        '/\bsome\b/i' => "Vagueness: 'some' has no measurable threshold.",
        '/\bvarious\b/i' => "Vagueness: 'various' is undefined in scope.",
        '/\buser[\s-]?friendly\b/i' => "Vagueness: 'user-friendly' is subjective.",
        '/\bfast\b/i' => "Vagueness: 'fast' requires a measurable threshold.",
        '/\bslow\b/i' => "Vagueness: 'slow' requires a measurable threshold.",
    ];

    $found = [];
    foreach ($patterns as $pattern => $description) {
        if (preg_match($pattern, $text)) {
            $found[] = $description;
        }
    }
    return $found;
}

function checkConformance(string $text): array
{
    $whenCount = preg_match_all('/\bWHEN\b/i', $text);
    $shallCount = preg_match_all('/\bTHE SYSTEM SHALL\b/i', $text);
    if ($whenCount >= 5 && $shallCount >= 5) {
        return [true, ''];
    }
    $missing = [];
    if ($whenCount < 5) {
        $missing[] = 'five WHEN clauses';
    }
    if ($shallCount < 5) {
        $missing[] = 'five THE SYSTEM SHALL clauses';
    }
    return [false, 'Missing: ' . implode(', ', $missing)];
}

function saveRequirement(PDO $db, array $row): void
{
    $stmt = $db->prepare("
        INSERT INTO requirements
        (req_id, group_name, participant_id, raw_input, structured_req, source_prompt, ai_response, effort_seconds,
         llm_duration_seconds, quality_duration_seconds, test_duration_seconds, error_message)
        VALUES
        (:req_id, :group_name, :participant_id, :raw_input, :structured_req, :source_prompt, :ai_response, :effort_seconds,
         :llm_duration_seconds, :quality_duration_seconds, :test_duration_seconds, :error_message)
    ");
    $stmt->execute($row);
}

function saveQuality(PDO $db, string $reqId, array $quality): void
{
    $stmt = $db->prepare("
        INSERT INTO quality_reports
        (req_id, smell_count, conformance, conformance_notes, smells_json)
        VALUES (:req_id, :smell_count, :conformance, :conformance_notes, :smells_json)
    ");
    $stmt->execute([
        'req_id' => $reqId,
        'smell_count' => (int)$quality['smell_count'],
        'conformance' => !empty($quality['conformance']) ? 1 : 0,
        'conformance_notes' => (string)($quality['conformance_notes'] ?? ''),
        'smells_json' => json_encode($quality['smells'] ?? [], JSON_THROW_ON_ERROR),
    ]);
}

function saveTestCases(PDO $db, string $reqId, array $tcIds, string $rawOutput): void
{
    $stmt = $db->prepare("INSERT INTO test_cases (tc_id, req_id, raw_output) VALUES (?, ?, ?)");
    foreach ($tcIds as $tcId) {
        $stmt->execute([$tcId, $reqId, $rawOutput]);
    }
}

function nextRequirementId(PDO $db, string $prefix): string
{
    $stmt = $db->prepare("SELECT COUNT(*) FROM requirements WHERE req_id LIKE ?");
    $stmt->execute([$prefix . '-%']);
    return sprintf('%s-%03d', $prefix, ((int)$stmt->fetchColumn()) + 1);
}

function nextTestCaseId(PDO $db, int $offset): string
{
    $count = (int)$db->query("SELECT COUNT(*) FROM test_cases")->fetchColumn();
    return sprintf('TC-%03d', $count + 1 + $offset);
}

function metrics(PDO $db, ?string $group = null): array
{
    $condition = $group ? 'WHERE r.group_name = :group' : '';
    $reqCondition = $group ? 'WHERE group_name = :group' : '';
    $params = $group ? ['group' => $group] : [];

    $reqStmt = $db->prepare("SELECT COUNT(*) FROM requirements {$reqCondition}");
    $reqStmt->execute($params);
    $total = (int)$reqStmt->fetchColumn();

    $qualityStmt = $db->prepare("
        SELECT AVG(q.smell_count), AVG(q.conformance)
        FROM quality_reports q
        JOIN requirements r ON r.req_id = q.req_id
        {$condition}
    ");
    $qualityStmt->execute($params);
    [$avgSmells, $conformanceRate] = $qualityStmt->fetch(PDO::FETCH_NUM) ?: [0, 0];

    $effortStmt = $db->prepare("SELECT AVG(effort_seconds) FROM requirements {$reqCondition}");
    $effortStmt->execute($params);
    $avgEffort = (float)($effortStmt->fetchColumn() ?: 0);

    $tcStmt = $db->prepare("
        SELECT COUNT(t.tc_id), COUNT(DISTINCT t.req_id)
        FROM test_cases t
        JOIN requirements r ON r.req_id = t.req_id
        {$condition}
    ");
    $tcStmt->execute($params);
    [$totalTcs, $traced] = $tcStmt->fetch(PDO::FETCH_NUM) ?: [0, 0];

    return [
        'total_reqs' => $total,
        'total_tcs' => (int)$totalTcs,
        'avg_smells' => round((float)($avgSmells ?? 0), 2),
        'conformance_rate' => round(((float)($conformanceRate ?? 0)) * 100, 1),
        'traceability_coverage' => $total ? round($traced / $total * 100, 1) : 0,
        'avg_effort' => round($avgEffort, 1),
        'avg_llm_time' => 0.0,
    ];
}

function requirementsWithQuality(PDO $db): array
{
    return $db->query("
        SELECT r.*, q.smell_count, q.conformance, q.conformance_notes, q.smells_json
        FROM requirements r
        LEFT JOIN quality_reports q ON q.req_id = r.req_id
        ORDER BY r.created_at DESC, r.req_id DESC
    ")->fetchAll(PDO::FETCH_ASSOC);
}

function logEvent(PDO $db, string $level, string $message, array $context = []): void
{
    $line = sprintf("%s | %-5s | %s | %s\n", date('Y-m-d H:i:s'), strtoupper($level), $message, json_encode($context));
    file_put_contents(LOG_PATH, $line, FILE_APPEND);
    $stmt = $db->prepare("INSERT INTO event_logs (level, message, context_json) VALUES (?, ?, ?)");
    $stmt->execute([$level, $message, json_encode($context)]);
}

function exportCsv(PDO $db, string $type): void
{
    $allowed = [
        'requirements' => "SELECT * FROM requirements ORDER BY created_at DESC",
        'quality' => "SELECT * FROM quality_reports ORDER BY created_at DESC",
        'test_cases' => "SELECT * FROM test_cases ORDER BY created_at DESC",
        'logs' => "SELECT * FROM event_logs ORDER BY created_at DESC",
    ];
    if (!isset($allowed[$type])) {
        http_response_code(404);
        exit('Unknown export.');
    }

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $type . '.csv"');
    $out = fopen('php://output', 'w');
    $rows = $db->query($allowed[$type]);
    $first = true;
    while ($row = $rows->fetch(PDO::FETCH_ASSOC)) {
        if ($first) {
            fputcsv($out, array_keys($row));
            $first = false;
        }
        fputcsv($out, $row);
    }
    fclose($out);
    exit;
}

function isParticipationAuthenticated(): bool
{
    return !empty($_SESSION['participation_authenticated']);
}

function isEvaluationAuthenticated(): bool
{
    return !empty($_SESSION['evaluation_authenticated']);
}

function isEvaluationPage(string $page): bool
{
    return in_array($page, ['history', 'traceability', 'dashboard', 'logs'], true);
}

function renderLogin(string $area, ?string $error): void
{
    $isEvaluation = $area === 'evaluation';
    $title = $isEvaluation ? 'Evaluation Area' : 'Study Participation';
    $message = $isEvaluation
        ? 'Enter the evaluation password to view study results.'
        : 'Enter the participation password to continue with the study task.';
    echo '<!doctype html><html lang="en"><head><meta charset="utf-8">';
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>' . h(APP_NAME) . '</title><link rel="stylesheet" href="assets/styles.css"></head>';
    echo '<body class="login-body"><main class="login-card">';
    echo '<h1>' . h($title) . '</h1><p>' . h($message) . '</p>';
    if ($error) {
        echo '<div class="notice error">' . h($error) . '</div>';
    }
    echo '<form method="post"><input type="hidden" name="action" value="login">';
    echo '<input type="hidden" name="area" value="' . h($area) . '">';
    echo '<label>Password<input type="password" name="password" required autofocus></label>';
    echo '<button class="primary" type="submit">Log In</button></form>';
    if ($isEvaluation) {
        echo '<p><a href="index.php">Go to participation login</a></p>';
    } else {
        echo '<p><a href="index.php?page=dashboard">Go to evaluation login</a></p>';
    }
    echo '</main></body></html>';
}

function renderPage(PDO $db, string $page, ?string $notice, ?string $error, ?array $result): void
{
    $pages = ['tool', 'control', 'history', 'traceability', 'dashboard', 'logs'];
    if (!in_array($page, $pages, true)) {
        $page = 'tool';
    }
    $toolMetrics = metrics($db, 'tool');
    $controlMetrics = metrics($db, 'control');

    echo '<!doctype html><html lang="en"><head><meta charset="utf-8">';
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>' . h(APP_NAME) . '</title><link rel="stylesheet" href="assets/styles.css"></head><body>';
    echo '<aside class="sidebar"><div class="brand">LLM RE Artefact</div><nav>';
    foreach ([
        'tool' => 'Guided ChatGPT',
        'control' => 'Control Group',
    ] as $key => $label) {
        $active = $page === $key ? ' active' : '';
        echo '<a class="' . $active . '" href="?page=' . h($key) . '">' . h($label) . '</a>';
    }
    echo '<div class="nav-label">Evaluation</div>';
    foreach ([
        'history' => 'History',
        'traceability' => 'Traceability',
        'dashboard' => 'Evaluation',
        'logs' => 'Logs',
    ] as $key => $label) {
        $active = $page === $key ? ' active' : '';
        echo '<a class="' . $active . '" href="?page=' . h($key) . '">' . h($label) . '</a>';
    }
    $links = [];
    $links[] = isParticipationAuthenticated()
        ? '<a href="?logout=participation">Log out participation</a>'
        : '<a href="index.php">Participation login</a>';
    $links[] = isEvaluationAuthenticated()
        ? '<a href="?logout=evaluation">Log out evaluation</a>'
        : '<a href="?page=dashboard">Evaluation login</a>';
    echo '</nav><div class="sidebar-foot">Mode: Guided ChatGPT<br>Data: SQLite<br>' . implode('<br>', $links) . '</div></aside>';
    echo '<main class="main">';
    echo '<header class="topbar"><div><h1>' . h(pageTitle($page)) . '</h1><p>' . h(pageSubtitle($page)) . '</p></div></header>';
    if ($notice) {
        echo '<div class="notice success">' . h($notice) . '</div>';
    }
    if ($error) {
        echo '<div class="notice error">' . h($error) . '</div>';
    }

    if ($page === 'tool') {
        renderToolForm($result);
    } elseif ($page === 'control') {
        renderControlForm($result);
    } elseif ($page === 'history') {
        renderHistory($db);
    } elseif ($page === 'traceability') {
        renderTraceability($db);
    } elseif ($page === 'dashboard') {
        renderDashboard($toolMetrics, $controlMetrics);
    } else {
        renderLogs($db);
    }
    echo '</main></body></html>';
}

function renderToolForm(?array $result): void
{
    echo '<section class="panel guide">';
    echo '<h2>Guided Study Task</h2>';
    echo '<p>All participants receive the same scenario and the same system prompt. First write your own requirements. Then copy the generated ChatGPT prompt, paste it into ChatGPT, and paste the full answer back here.</p>';
    echo '<h3>Scenario</h3><pre>' . h(STUDY_CASE) . '</pre>';
    echo '<div class="step-grid">';
    echo '<div><strong>1</strong><span>Write your own requirements for the scenario.</span></div>';
    echo '<div><strong>2</strong><span>Copy the generated prompt with the fixed instructions.</span></div>';
    echo '<div><strong>3</strong><span>Paste it into ChatGPT without changing it.</span></div>';
    echo '<div><strong>4</strong><span>Paste the complete answer and save it.</span></div>';
    echo '</div>';
    echo '<h3>Fixed System Prompt</h3><pre>' . h(standardizedSystemPrompt()) . '</pre>';
    echo '</section>';

    echo '<section class="panel"><form method="post"><input type="hidden" name="action" value="save_tool">';
    echo '<div class="form-grid"><label>Participant ID<input name="participant_id" placeholder="P01"></label>';
    echo '<label>Manual effort in seconds<input name="effort_seconds" type="number" min="0" value="0"></label></div>';
    echo '<label>Your drafted requirements<textarea id="participantRequirements" name="raw_input" rows="10" required placeholder="Write your own initial requirements for the university exam registration system."></textarea></label>';
    echo '<label>Generated ChatGPT prompt<textarea id="studyPrompt" rows="20" readonly placeholder="The standardized prompt appears here after you enter your requirements."></textarea></label>';
    echo '<div class="actions"><button class="secondary" type="button" onclick="copyPrompt()">Copy Prompt</button><a href="https://chatgpt.com/" target="_blank" rel="noopener">Open ChatGPT</a></div>';
    echo '<label>Complete ChatGPT response<textarea name="ai_response" rows="16" required placeholder="Paste the complete ChatGPT response here. Do not rewrite or summarize it."></textarea></label>';
    echo '<button class="primary" type="submit">Save Guided Result</button></form></section>';
    if ($result) {
        echo '<section class="panel result"><h2>' . h($result['req_id']) . '</h2>';
        echo '<div class="metric-row"><span>Recorded effort: ' . h((string)$result['duration']) . ' s</span><span>Smells: ' . h((string)$result['quality']['smell_count']) . '</span><span>Conformance: ' . ($result['quality']['conformance'] ? 'Pass' : 'Fail') . '</span></div>';
        echo '<h3>Structured Requirements</h3><pre>' . h($result['structured_req']) . '</pre>';
        echo '<h3>Acceptance Test Cases</h3><pre>' . h($result['test_cases']) . '</pre>';
        echo '<h3>Quality Findings</h3>' . smellList($result['quality']);
        echo '</section>';
    }
    echo '<script>
    const systemPrompt = ' . json_encode(standardizedSystemPrompt()) . ';
    const reqInput = document.getElementById("participantRequirements");
    const promptBox = document.getElementById("studyPrompt");
    reqInput.value = window.sessionStorage.getItem("guided_requirements_draft") || "";
    function buildPrompt() {
      const requirements = reqInput.value.trim();
      window.sessionStorage.setItem("guided_requirements_draft", reqInput.value);
      promptBox.value = requirements
        ? systemPrompt + "\n\nParticipant requirements:\n\"\"\"" + requirements + "\"\"\""
        : "";
    }
    reqInput.addEventListener("input", buildPrompt);
    buildPrompt();
    function copyPrompt() {
      const prompt = document.getElementById("studyPrompt");
      if (!prompt.value.trim()) {
        reqInput.focus();
        return;
      }
      prompt.select();
      prompt.setSelectionRange(0, 999999);
      const done = function () {
        document.body.classList.add("copied");
        window.setTimeout(function () { document.body.classList.remove("copied"); }, 1400);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(prompt.value).then(done);
      } else {
        document.execCommand("copy");
        done();
      }
    }
    </script>';
}

function renderControlForm(?array $result): void
{
    echo '<section class="panel"><form method="post"><input type="hidden" name="action" value="save_control">';
    echo '<h2>Manual Baseline Task</h2><p>Use the same scenario, but do not use ChatGPT or another AI tool. Write the structured requirements manually and save the result.</p>';
    echo '<h3>Scenario</h3><pre>' . h(STUDY_CASE) . '</pre>';
    echo '<div class="form-grid"><label>Participant ID<input name="participant_id" placeholder="P01"></label>';
    echo '<label>Manual effort in seconds<input name="effort_seconds" type="number" min="0" value="0"></label></div>';
    echo '<label>Manual structured requirements<textarea name="raw_input" rows="12" required placeholder="Write the manual structured requirements here."></textarea></label>';
    echo '<button class="primary" type="submit">Evaluate and Save</button></form></section>';
    if ($result) {
        echo '<section class="panel result"><h2>' . h($result['req_id']) . '</h2>';
        echo '<div class="metric-row"><span>Smells: ' . h((string)$result['quality']['smell_count']) . '</span><span>Conformance: ' . ($result['quality']['conformance'] ? 'Pass' : 'Fail') . '</span></div>';
        echo '<h3>Quality Findings</h3>' . smellList($result['quality']) . '</section>';
    }
}

function renderHistory(PDO $db): void
{
    $rows = requirementsWithQuality($db);
    echo '<section class="panel"><div class="actions">' . exportLinks() . '</div>';
    if (!$rows) {
        echo '<p>No requirements have been stored yet.</p></section>';
        return;
    }
    foreach ($rows as $row) {
        echo '<details class="history-item"><summary><strong>' . h($row['req_id']) . '</strong> ' . h($row['group_name']) . ' | smells: ' . h((string)$row['smell_count']) . ' | ' . h($row['created_at']) . '</summary>';
        echo '<div class="two-col"><div><h3>Study Input</h3><p>' . nl2br(h($row['raw_input'])) . '</p></div><div><h3>Structured Requirements</h3><pre>' . h($row['structured_req'] ?: '-') . '</pre></div></div>';
        if (!empty($row['ai_response'])) {
            echo '<h3>Full ChatGPT Response</h3><pre>' . h((string)$row['ai_response']) . '</pre>';
        }
        echo '<h3>Quality</h3><p>Conformance: ' . ((int)$row['conformance'] ? 'Pass' : 'Fail') . '. ' . h((string)$row['conformance_notes']) . '</p>';
        echo '</details>';
    }
    echo '</section>';
}

function renderTraceability(PDO $db): void
{
    $rows = $db->query("
        SELECT r.req_id, r.structured_req, t.tc_id
        FROM requirements r
        LEFT JOIN test_cases t ON t.req_id = r.req_id
        ORDER BY r.req_id, t.tc_id
    ")->fetchAll(PDO::FETCH_ASSOC);
    echo '<section class="panel"><table><thead><tr><th>Requirement</th><th>Linked Test Case</th><th>Coverage</th></tr></thead><tbody>';
    foreach ($rows as $row) {
        $covered = $row['tc_id'] ? 'Covered' : 'Missing';
        echo '<tr><td>' . h($row['req_id']) . '</td><td>' . h($row['tc_id'] ?: '-') . '</td><td><span class="pill ' . ($row['tc_id'] ? 'ok' : 'bad') . '">' . $covered . '</span></td></tr>';
    }
    echo '</tbody></table></section>';
}

function renderDashboard(array $tool, array $control): void
{
    echo '<section class="metric-cards">';
    foreach ([
        ['Tool Requirements', $tool['total_reqs']],
        ['Control Requirements', $control['total_reqs']],
        ['Tool Conformance', $tool['conformance_rate'] . '%'],
        ['Control Conformance', $control['conformance_rate'] . '%'],
    ] as $card) {
        echo '<div class="metric-card"><span>' . h($card[0]) . '</span><strong>' . h((string)$card[1]) . '</strong></div>';
    }
    echo '</section><section class="panel"><h2>Comparative Evaluation</h2><table><thead><tr><th>Metric</th><th>Tool Group</th><th>Control Group</th><th>Delta</th></tr></thead><tbody>';
    $rows = [
        ['Average smell count', $tool['avg_smells'], $control['avg_smells'], round($control['avg_smells'] - $tool['avg_smells'], 2)],
        ['Conformance rate', $tool['conformance_rate'] . '%', $control['conformance_rate'] . '%', round($tool['conformance_rate'] - $control['conformance_rate'], 1) . '%'],
        ['Traceability coverage', $tool['traceability_coverage'] . '%', $control['traceability_coverage'] . '%', round($tool['traceability_coverage'] - $control['traceability_coverage'], 1) . '%'],
        ['Average manual effort', $tool['avg_effort'] . ' s', $control['avg_effort'] . ' s', round($control['avg_effort'] - $tool['avg_effort'], 1) . ' s'],
    ];
    foreach ($rows as $row) {
        echo '<tr><td>' . h($row[0]) . '</td><td>' . h((string)$row[1]) . '</td><td>' . h((string)$row[2]) . '</td><td>' . h((string)$row[3]) . '</td></tr>';
    }
    echo '</tbody></table><div class="actions">' . exportLinks() . '</div></section>';
}

function renderLogs(PDO $db): void
{
    $rows = $db->query("SELECT * FROM event_logs ORDER BY created_at DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
    echo '<section class="panel"><div class="actions">' . exportLinks() . '</div><table><thead><tr><th>Time</th><th>Level</th><th>Message</th><th>Context</th></tr></thead><tbody>';
    foreach ($rows as $row) {
        echo '<tr><td>' . h($row['created_at']) . '</td><td>' . h($row['level']) . '</td><td>' . h($row['message']) . '</td><td><code>' . h((string)$row['context_json']) . '</code></td></tr>';
    }
    echo '</tbody></table></section>';
}

function exportLinks(): string
{
    return '<a href="?export=requirements">Requirements CSV</a><a href="?export=quality">Quality CSV</a><a href="?export=test_cases">Test Cases CSV</a><a href="?export=logs">Logs CSV</a>';
}

function smellList(array $quality): string
{
    $smells = $quality['smells'] ?? [];
    if (!$smells) {
        return '<p>No smells detected.</p>';
    }
    $html = '<ul>';
    foreach ($smells as $smell) {
        $html .= '<li>' . h((string)$smell) . '</li>';
    }
    return $html . '</ul>';
}

function pageTitle(string $page): string
{
    return [
        'tool' => 'Guided ChatGPT Workflow',
        'control' => 'Control Group Capture',
        'history' => 'Artefact History',
        'traceability' => 'Traceability Matrix',
        'dashboard' => 'Evaluation Dashboard',
        'logs' => 'Evaluation Logs',
    ][$page] ?? APP_NAME;
}

function pageSubtitle(string $page): string
{
    return [
        'tool' => 'Use one standardized prompt in ChatGPT and paste the response back for local evaluation.',
        'control' => 'Capture baseline requirements without LLM support for comparative evaluation.',
        'history' => 'Review stored requirements, structured outputs, quality reports, and versions.',
        'traceability' => 'Inspect explicit links between requirements and acceptance test cases.',
        'dashboard' => 'Compare template conformance, smell density, traceability coverage, and effort.',
        'logs' => 'Inspect operational events captured during the study.',
    ][$page] ?? '';
}

function cleanId(string $value): string
{
    return preg_replace('/[^A-Za-z0-9_-]/', '', trim($value)) ?? '';
}

function elapsed(float $start): float
{
    return round(microtime(true) - $start, 2);
}

function h(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
?>
