Set-Location C:\\Users\\khali\\Desktop\\openFDA

# Variables
$FDA_part = Read-Host "Please enter which FDA part to query device, drug"
$database = Read-Host "Please select the database from udi, event, enforcement, 510k, ndc"
$search = Read-Host "Please enter your query"
$limit = 100

# request
$url = "https://api.fda.gov/$FDA_part/$database.json?search=$search&limit=$limit"

$meta = Invoke-WebRequest $url |
ConvertFrom-Json |
Select-Object -expand meta

$n_results = $meta.results.total

if ($n_results -gt 100) {
    $n_skips = [math]::ceiling($n_results / 100) - 1
}

else {
    $n_skips = 0
}

$urls = @() # create an empty list
foreach ($i in 0..$n_skips) {
    $skip = 100 * $i
    $skip_url = "https://api.fda.gov/$FDA_part/$database.json?search=$search&limit=$limit&skip=$skip"
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