<?php
// Get list of JSON files from data directory
$dataDir = __DIR__ . '/data';
$jsonFiles = glob($dataDir . '/*.json');

// Sort by modified time (newest first)
usort($jsonFiles, function($a, $b) {
    return filemtime($b) - filemtime($a);
});

// Get selected file or default to newest
$selectedFile = isset($_GET['file']) ? $_GET['file'] : (count($jsonFiles) > 0 ? basename($jsonFiles[0]) : '');
$currentFilePath = $dataDir . '/' . $selectedFile;

// Load JSON data
$jobs = [];
$error = '';
if ($selectedFile && file_exists($currentFilePath)) {
    $jsonContent = file_get_contents($currentFilePath);
    $jobs = json_decode($jsonContent, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        $error = 'Error parsing JSON: ' . json_last_error_msg();
    }
} elseif ($selectedFile) {
    $error = 'File not found: ' . htmlspecialchars($selectedFile);
}

// Get file metadata
$fileInfo = '';
if ($selectedFile && file_exists($currentFilePath)) {
    $fileSize = filesize($currentFilePath);
    $fileDate = date('F d, Y H:i:s', filemtime($currentFilePath));
    $fileInfo = sprintf('%s (%.2f KB, %s)', $selectedFile, $fileSize / 1024, $fileDate);
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Scraper Results Viewer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8 max-w-7xl">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">🔍 Job Scraper Results</h1>
            <p class="text-gray-600">View and filter job listings from various sources</p>
        </div>

        <!-- File selector and stats -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div class="flex-1">
                    <label for="fileSelect" class="block text-sm font-medium text-gray-700 mb-2">
                        Select JSON File:
                    </label>
                    <select 
                        id="fileSelect" 
                        onchange="window.location.href='?file=' + this.value"
                        class="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <?php if (count($jsonFiles) === 0): ?>
                            <option value="">No JSON files found</option>
                        <?php else: ?>
                            <?php foreach ($jsonFiles as $file): ?>
                                <?php 
                                    $basename = basename($file);
                                    $selected = ($basename === $selectedFile) ? 'selected' : '';
                                    $date = date('Y-m-d H:i', filemtime($file));
                                    $size = filesize($file) / 1024;
                                ?>
                                <option value="<?= htmlspecialchars($basename) ?>" <?= $selected ?>>
                                    <?= htmlspecialchars($basename) ?> (<?= $date ?>, <?= number_format($size, 2) ?> KB)
                                </option>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </select>
                </div>

                <?php if (!empty($jobs)): ?>
                <div class="flex gap-4">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-center">
                        <div class="text-2xl font-bold text-blue-700"><?= count($jobs) ?></div>
                        <div class="text-xs text-blue-600 uppercase">Total Jobs</div>
                    </div>
                    <?php 
                        $sources = array_count_values(array_column($jobs, 'source'));
                    ?>
                    <div class="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-center">
                        <div class="text-2xl font-bold text-green-700"><?= count($sources) ?></div>
                        <div class="text-xs text-green-600 uppercase">Sources</div>
                    </div>
                </div>
                <?php endif; ?>
            </div>

            <?php if ($fileInfo): ?>
            <div class="mt-4 text-sm text-gray-600 bg-gray-50 rounded px-4 py-2">
                📄 <?= htmlspecialchars($fileInfo) ?>
            </div>
            <?php endif; ?>
        </div>

        <!-- Error message -->
        <?php if ($error): ?>
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <div class="flex items-center">
                <span class="text-red-700 font-medium">⚠️ <?= htmlspecialchars($error) ?></span>
            </div>
        </div>
        <?php endif; ?>

        <!-- Jobs table -->
        <?php if (!empty($jobs)): ?>
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-8">
                                #
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Job Title
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Company
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Location
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Salary
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Source
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Scraped At
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                                Action
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <?php foreach ($jobs as $index => $job): ?>
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <?= $index + 1 ?>
                            </td>
                            <td class="px-6 py-4 nonwrap">
                                <div class="text-sm font-medium text-gray-900 max-w-md no-wrap">
                                    <?= htmlspecialchars($job['title'] ?? 'N/A') ?>
                                </div>
                                <?php if (!empty($job['description']) && strlen($job['description']) > 0): ?>
                                <div class="text-xs text-gray-500 mt-1 line-clamp-2">
                                    <?= htmlspecialchars(substr($job['description'], 0, 100)) ?>
                                    <?= strlen($job['description']) > 100 ? '...' : '' ?>
                                </div>
                                <?php endif; ?>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm text-gray-900 text-ellipsis overflow-hidden max-w-xs">
                                    <?= htmlspecialchars($job['company'] ?? 'N/A') ?>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm text-gray-900">
                                    <?= htmlspecialchars($job['location'] ?? 'N/A') ?>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <?php if (!empty($job['salary'])): ?>
                                <span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                                    <?= htmlspecialchars($job['salary']) ?>
                                </span>
                                <?php else: ?>
                                <span class="text-sm text-gray-400">-</span>
                                <?php endif; ?>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <?php 
                                    $sourceColors = [
                                        'LinkedIn' => 'bg-blue-100 text-blue-800',
                                        'Indeed' => 'bg-purple-100 text-purple-800',
                                        'Jobs.ac.uk' => 'bg-orange-100 text-orange-800',
                                        'DWP' => 'bg-indigo-100 text-indigo-800',
                                        'KTP' => 'bg-pink-100 text-pink-800',
                                    ];
                                    $source = $job['source'] ?? 'Unknown';
                                    $colorClass = $sourceColors[$source] ?? 'bg-gray-100 text-gray-800';
                                ?>
                                <span class="px-2 py-1 text-xs font-semibold rounded-full <?= $colorClass ?>">
                                    <?= htmlspecialchars($source) ?>
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <?= htmlspecialchars($job['scraped_at'] ?? 'N/A') ?>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">
                                <?php if (!empty($job['url'])): ?>
                                <a 
                                    href="<?= htmlspecialchars($job['url']) ?>" 
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="inline-flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors"
                                >
                                    View Job
                                    <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                                    </svg>
                                </a>
                                <?php else: ?>
                                <span class="text-gray-400">No URL</span>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Summary footer -->
        <div class="mt-6 bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">📊 Summary by Source</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <?php 
                    $sourceCounts = array_count_values(array_column($jobs, 'source'));
                    arsort($sourceCounts);
                    foreach ($sourceCounts as $source => $count): 
                        $sourceColors = [
                            'LinkedIn' => 'border-blue-500 bg-blue-50',
                            'Indeed' => 'border-purple-500 bg-purple-50',
                            'Jobs.ac.uk' => 'border-orange-500 bg-orange-50',
                            'DWP' => 'border-indigo-500 bg-indigo-50',
                            'KTP' => 'border-pink-500 bg-pink-50',
                        ];
                        $colorClass = $sourceColors[$source] ?? 'border-gray-500 bg-gray-50';
                ?>
                <div class="border-l-4 <?= $colorClass ?> p-4 rounded">
                    <div class="text-2xl font-bold text-gray-800"><?= $count ?></div>
                    <div class="text-sm text-gray-600"><?= htmlspecialchars($source) ?></div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <?php elseif (!$error && $selectedFile): ?>
        <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
            <div class="flex items-center">
                <span class="text-yellow-700 font-medium">ℹ️ No jobs found in the selected file.</span>
            </div>
        </div>
        <?php endif; ?>

        <!-- Footer -->
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>Job Scraper Results Viewer | Last updated: <?= date('Y-m-d H:i:s') ?></p>
        </div>
    </div>
</body>
</html>