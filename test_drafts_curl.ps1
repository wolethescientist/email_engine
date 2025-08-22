# PowerShell script to test draft functionality using curl
# Make sure your email engine is running on http://localhost:8000

$BASE_URL = "http://localhost:8000"
$AUTH_TOKEN = ""  # Set your auth token here if needed

# Function to make authenticated requests
function Invoke-ApiRequest {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,
        [string]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    $headers = @{}
    if ($AUTH_TOKEN) {
        $headers["Authorization"] = "Bearer $AUTH_TOKEN"
    }
    $headers["Content-Type"] = $ContentType
    
    $params = @{
        Uri = "$BASE_URL$Endpoint"
        Method = $Method
        Headers = $headers
    }
    
    if ($Body) {
        $params.Body = $Body
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    }
    catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response: $responseBody" -ForegroundColor Red
        }
        return $null
    }
}

# Test functions
function Test-CreateDraft {
    Write-Host "`n=== Creating Test Draft ===" -ForegroundColor Yellow
    
    $draftData = @{
        subject = "Test Draft - PowerShell Debug"
        body = "This is a test draft created via PowerShell for debugging."
        to = @("test@example.com")
        cc = @()
        bcc = @()
        attachments = @()
    } | ConvertTo-Json -Depth 3
    
    Write-Host "Draft data:" -ForegroundColor Cyan
    Write-Host $draftData
    
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/emails/compose" -Body $draftData
    if ($result) {
        Write-Host "✅ Draft created successfully with ID: $($result.id)" -ForegroundColor Green
        return $result.id
    } else {
        Write-Host "❌ Failed to create draft" -ForegroundColor Red
        return $null
    }
}

function Test-CreateDraftWithAttachment {
    Write-Host "`n=== Creating Test Draft with Attachment ===" -ForegroundColor Yellow
    
    # Create a simple text attachment
    $textContent = "This is a test attachment for debugging."
    $textBytes = [System.Text.Encoding]::UTF8.GetBytes($textContent)
    $textBase64 = [System.Convert]::ToBase64String($textBytes)
    
    $draftData = @{
        subject = "Test Draft with Attachment - PowerShell Debug"
        body = "This draft has a test attachment."
        to = @("test@example.com")
        cc = @()
        bcc = @()
        attachments = @(
            @{
                filename = "test_attachment.txt"
                content_base64 = $textBase64
                content_type = "text/plain"
            }
        )
    } | ConvertTo-Json -Depth 3
    
    Write-Host "Creating draft with attachment..."
    
    $result = Invoke-ApiRequest -Method "POST" -Endpoint "/emails/compose" -Body $draftData
    if ($result) {
        Write-Host "✅ Draft with attachment created successfully with ID: $($result.id)" -ForegroundColor Green
        return $result.id
    } else {
        Write-Host "❌ Failed to create draft with attachment" -ForegroundColor Red
        return $null
    }
}

function Test-GetDrafts {
    Write-Host "`n=== Getting Drafts ===" -ForegroundColor Yellow
    
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/emails/drafts"
    if ($result) {
        Write-Host "✅ Retrieved drafts: $($result.total) total" -ForegroundColor Green
        Write-Host ($result | ConvertTo-Json -Depth 5)
        return $result
    } else {
        Write-Host "❌ Failed to get drafts" -ForegroundColor Red
        return $null
    }
}

function Test-DebugAllEmails {
    Write-Host "`n=== Getting Debug Information ===" -ForegroundColor Yellow
    
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/emails/debug/all-emails"
    if ($result) {
        Write-Host "✅ Debug info - Total emails: $($result.total_emails)" -ForegroundColor Green
        Write-Host "   Folders: $($result.folders -join ', ')"
        Write-Host "   Drafts count: $($result.drafts_count)"
        Write-Host ($result | ConvertTo-Json -Depth 5)
        return $result
    } else {
        Write-Host "❌ Failed to get debug info" -ForegroundColor Red
        return $null
    }
}

function Test-DebugDraftsDetailed {
    Write-Host "`n=== Getting Detailed Draft Information ===" -ForegroundColor Yellow
    
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/emails/debug/drafts-detailed"
    if ($result) {
        Write-Host "✅ Detailed draft info - Total drafts: $($result.total_drafts)" -ForegroundColor Green
        Write-Host ($result | ConvertTo-Json -Depth 5)
        return $result
    } else {
        Write-Host "❌ Failed to get detailed draft info" -ForegroundColor Red
        return $null
    }
}

function Test-GetDraftDetail {
    param([int]$DraftId)
    
    Write-Host "`n=== Getting Draft $DraftId Details ===" -ForegroundColor Yellow
    
    $result = Invoke-ApiRequest -Method "GET" -Endpoint "/emails/$DraftId" -Body "folder=drafts"
    if ($result) {
        Write-Host "✅ Retrieved draft $DraftId details" -ForegroundColor Green
        Write-Host ($result | ConvertTo-Json -Depth 5)
        return $result
    } else {
        Write-Host "❌ Failed to get draft $DraftId details" -ForegroundColor Red
        return $null
    }
}

function Run-FullTest {
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host "EMAIL ENGINE DRAFT DEBUG TEST (PowerShell)" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
    
    # Step 1: Check current state
    Write-Host "`n1. Checking current drafts..." -ForegroundColor Cyan
    Test-GetDrafts | Out-Null
    
    # Step 2: Get debug information
    Write-Host "`n2. Getting debug information..." -ForegroundColor Cyan
    Test-DebugAllEmails | Out-Null
    
    # Step 3: Create test draft
    Write-Host "`n3. Creating test draft..." -ForegroundColor Cyan
    $newDraftId = Test-CreateDraft
    
    # Step 4: Create draft with attachment
    Write-Host "`n4. Creating test draft with attachment..." -ForegroundColor Cyan
    $newDraftWithAttachmentId = Test-CreateDraftWithAttachment
    
    # Step 5: Check drafts again
    Write-Host "`n5. Checking drafts after creation..." -ForegroundColor Cyan
    Test-GetDrafts | Out-Null
    
    # Step 6: Get detailed draft information
    Write-Host "`n6. Getting detailed draft information..." -ForegroundColor Cyan
    Test-DebugDraftsDetailed | Out-Null
    
    # Step 7: Test specific draft retrieval
    if ($newDraftId) {
        Write-Host "`n7. Getting details for draft $newDraftId..." -ForegroundColor Cyan
        Test-GetDraftDetail -DraftId $newDraftId | Out-Null
    }
    
    Write-Host "`n" + ("=" * 60) -ForegroundColor Magenta
    Write-Host "TEST COMPLETE" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
}

# Main menu
function Show-Menu {
    Write-Host "`nEmail Engine Draft Debugger (PowerShell)" -ForegroundColor Green
    Write-Host "=" * 40 -ForegroundColor Green
    Write-Host "Make sure your email engine is running on http://localhost:8000"
    Write-Host "You may need to set an authentication token if your API requires it."
    
    Write-Host "`nChoose an option:" -ForegroundColor Yellow
    Write-Host "1. Run full test"
    Write-Host "2. Create simple test draft"
    Write-Host "3. Create test draft with attachment"
    Write-Host "4. Get current drafts"
    Write-Host "5. Get debug information"
    Write-Host "6. Get detailed draft information"
    Write-Host "7. Exit"
}

# Main execution
if ($AUTH_TOKEN -eq "") {
    $inputToken = Read-Host "`nEnter your auth token (press Enter if not needed)"
    if ($inputToken) {
        $AUTH_TOKEN = $inputToken
    }
}

do {
    Show-Menu
    $choice = Read-Host "`nEnter your choice (1-7)"
    
    switch ($choice) {
        "1" { Run-FullTest }
        "2" { Test-CreateDraft | Out-Null }
        "3" { Test-CreateDraftWithAttachment | Out-Null }
        "4" { Test-GetDrafts | Out-Null }
        "5" { Test-DebugAllEmails | Out-Null }
        "6" { Test-DebugDraftsDetailed | Out-Null }
        "7" { Write-Host "Exiting..." -ForegroundColor Green; break }
        default { Write-Host "Invalid choice" -ForegroundColor Red }
    }
} while ($true)