Set-Location E:\\Scripts\\open_FDA

# Variables

$database = Read-Host "Please select the database from udi, event, enforcement, 510k"
$search = Read-Host "Please enter your query"

$limit = 100


# request
$url = "https://api.fda.gov/device/$database.json?search=$search&limit=$limit"


$response = Invoke-WebRequest -Uri $url -UseBasicParsing 

$response = $response.StatusDescription

if ($response -eq "OK") {
    $meta = Invoke-WebRequest -Uri $url -UseBasicParsing|
    ConvertFrom-Json |
    Select-Object -expand meta

    $n_results = $meta.results.total
    $update = $meta.last_updated
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
    $results = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data_content = $results.Content
    $fda_data += $data_content
}



$fda_data |
Out-File "data_fda_$update.json"

Invoke-Item "data_fda_$update.json"
