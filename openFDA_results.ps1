# Variables

$PSScriptRoot

$search = Read-Host 'Please enter your query,
-       "+" for OR operation, 
-       "+AND+" for "AND" operation'

$limit = 1000


# request
$url = "https://api.fda.gov/device/event.json?search=$search&limit=$limit"


$response = Invoke-WebRequest -Uri $url -UseBasicParsing 

$response = $response.StatusDescription

if ($response -eq "OK") {
    $meta = Invoke-WebRequest -Uri $url -UseBasicParsing|
    ConvertFrom-Json |
    Select-Object -expand meta

    $n_results = $meta.results.total
    $update = $meta.last_updated
}

Write-Output("The search found $n_results mathces")

$results = Invoke-WebRequest -Uri $url  -UseBasicParsing 
$data_content = $results.Content | ConvertFrom-Json | Select-Object -expand results

$date =  $data_content | Select-Object report_number, date_received
$manufacturer = $data_content | Select-Object report_number, manufacturer_g1_name
$product_problems = $data_content | Select-Object report_number, product_problems

$devices = $f_data| Select-Object report_number, device
$devices 
$patients = $data_content | Select-Object report_number, patient
$mdr_texts = $data_content | Select-Object report_number, mdr_text


# $data_content | ConvertTo-Json -Depth 6| Out-File "data_fda_$update.json" -Encoding "UTF8" #  depth to unsure that no information is packed in a @{} format


# # |ForEach-Object { [System.Text.RegularExpressions.Regex]::Unescape($_) } | to escape unicode \uxxxx charecters, lots of error from double cotes ...

# Invoke-Item "data_fda_$update.json"