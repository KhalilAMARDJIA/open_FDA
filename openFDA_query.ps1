Set-Location C:\\Users\\khali\\Desktop\\openFDA

# Variables

# $database = Read-Host "Please select the database from udi, event, enforcement, 510k"
# $search = Read-Host "Please enter your query"
$database = "udi"
$search = "in2bones+AND+PIT'STOP"
$limit = 100

# request
$url = "https://api.fda.gov/device/$database.json?search=$search&limit=$limit"
$response = Invoke-WebRequest $url
$response = $response.StatusDescription

if ($response -eq "OK") {
    $meta = Invoke-WebRequest $url |
    ConvertFrom-Json |
    Select-Object -expand meta

    $n_results = $meta.results.total
}

if ($n_results -gt 100) {
    $n_skips = [math]::ceiling($n_results / 100) - 1
}

else {
    $n_skips = 0
}

$urls = @() # create an empty list

foreach ($i in 0..$n_skips) {
    $skip = 100 * $i
    $skip_url = "https://api.fda.gov/device/$database.json?search=$search&limit=$limit&skip=$skip"
    $urls += $skip_url
}

$fda_data = @()

foreach ($url in $urls) {
    $results = Invoke-WebRequest $url |
    ConvertFrom-Json |
    Select-Object -expand results
    $fda_data += $results
}

$fda_data |
ConvertTo-Json | 
Out-File "data_fda.json"

.\data_fda.json