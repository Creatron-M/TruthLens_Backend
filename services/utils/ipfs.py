import os
import json
import requests
from io import BytesIO

def put_json(obj: dict) -> str:
    """Upload JSON object to Pinata IPFS"""
    jwt_token = os.getenv('PINATA_JWT')
    
    if not jwt_token:
        print("❌ PINATA_JWT not configured - skipping IPFS upload")
        return ""
    
    try:
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "pinataContent": obj,
            "pinataMetadata": {
                "name": f"TruthLens-Attestation-{obj.get('marketId', 'unknown')}"
            },
            "pinataOptions": {
                "cidVersion": 1
            }
        }
        
        print("📤 Uploading metadata to Pinata IPFS...")
        response = requests.post(
            'https://api.pinata.cloud/pinning/pinJSONToIPFS',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            cid = result.get('IpfsHash')
            ipfs_url = f"ipfs://{cid}"
            print(f"✅ Uploaded to Pinata IPFS: {ipfs_url}")
            print(f"   View at: https://gateway.pinata.cloud/ipfs/{cid}")
            return ipfs_url
        else:
            print(f"❌ Pinata upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Try alternative approach for 403 errors
            if response.status_code == 403:
                print("   Trying alternative Pinata endpoint...")
                return upload_via_pinata_file_api(obj, jwt_token)
            
            return ""
            
    except Exception as e:
        print(f"❌ Pinata upload error: {e}")
        return ""
    
    try:
        # Prepare the JSON data as a file
        json_data = json.dumps(obj, indent=2)
        json_bytes = json_data.encode('utf-8')
        
        # Create file-like object
        files = {
            'file': ('metadata.json', BytesIO(json_bytes), 'application/json')
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print("📤 Uploading metadata to IPFS via Web3.Storage...")
        # Try the new Storacha API endpoint first
        try:
            response = requests.post(
                'https://up.web3.storage/upload',
                headers=headers,
                files=files,
                timeout=30
            )
        except requests.exceptions.RequestException:
            # Fallback to legacy endpoint
            response = requests.post(
                'https://api.web3.storage/upload',
                headers=headers,
                files=files,
                timeout=30
            )
        
        response.raise_for_status()
        result = response.json()
        cid = result.get('cid', '')
        
        if cid:
            ipfs_url = f"ipfs://{cid}"
            print(f"✅ Uploaded to IPFS: {ipfs_url}")
            print(f"   View at: https://{cid}.ipfs.w3s.link/metadata.json")
            return ipfs_url
        else:
            print("❌ No CID returned from Web3.Storage")
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"❌ IPFS upload failed: {e}")
        return ""

def test_pinata():
    """Test Pinata IPFS API connection"""
    jwt_token = os.getenv('PINATA_JWT')
    
    if not jwt_token:
        print("❌ Pinata JWT token not configured")
        return False
    
    try:
        # First test authentication
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.get(
            'https://api.pinata.cloud/data/testAuthentication',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', 'Unknown')
            print(f"✅ Pinata authentication: {message}")
            
            # Test upload with sample data
            import time
            test_data = {
                "service": "TruthLens", 
                "test": True,
                "timestamp": time.time()
            }
            
            upload_result = put_json(test_data)
            if upload_result and upload_result.startswith('ipfs://'):
                return True
            else:
                print("❌ Pinata test upload failed")
                return False
        else:
            print(f"❌ Pinata authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Pinata test error: {e}")
        return False

def upload_via_pinata_file_api(obj: dict, jwt_token: str) -> str:
    """Alternative Pinata upload using file API"""
    try:
        # Convert JSON to file-like object
        json_data = json.dumps(obj, indent=2)
        json_bytes = json_data.encode('utf-8')
        
        files = {
            'file': ('metadata.json', BytesIO(json_bytes), 'application/json')
        }
        
        # Metadata for the file
        pinata_metadata = json.dumps({
            'name': f'TruthLens-Attestation-{obj.get("marketId", "unknown")}',
            'keyvalues': {
                'service': 'TruthLens',
                'type': 'attestation-metadata'
            }
        })
        
        data = {
            'pinataMetadata': pinata_metadata,
            'pinataOptions': json.dumps({'cidVersion': 1})
        }
        
        headers = {
            'Authorization': f'Bearer {jwt_token}'
        }
        
        print("   📤 Trying Pinata file upload API...")
        response = requests.post(
            'https://api.pinata.cloud/pinning/pinFileToIPFS',
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            cid = result.get('IpfsHash')
            if cid:
                ipfs_url = f"ipfs://{cid}"
                print(f"✅ Alternative upload successful: {ipfs_url}")
                return ipfs_url
        else:
            print(f"   ❌ Alternative upload also failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Alternative upload error: {e}")
    
    return ""

def setup_web3_storage():
    """Helper function to guide users through Web3.Storage setup"""
    print("\n🌐 Web3.Storage Setup Guide:")
    print("1. Go to https://web3.storage/")
    print("2. Sign up with email or GitHub")
    print("3. Go to 'Account' → 'Create a token'")
    print("4. Copy the token and add to your .env file:")
    print("   WEB3STORAGE_TOKEN=your_token_here")
    print("5. Free tier includes 5GB storage + unlimited bandwidth")
    print("")

def test_web3_storage():
    """Test Web3.Storage connection"""
    token = os.getenv('WEB3STORAGE_TOKEN')
    if not token:
        print("❌ No Web3.Storage token configured")
        setup_web3_storage()
        return False
    
    try:
        # Test upload with small JSON
        test_data = {"test": "connection", "timestamp": "2025-10-30"}
        result = put_json(test_data)
        
        if result:
            print("✅ Web3.Storage connection successful!")
            return True
        else:
            print("❌ Web3.Storage test failed")
            return False
            
    except Exception as e:
        print(f"❌ Web3.Storage test error: {e}")
        return False

# Alternative IPFS Provider Functions

# Pinata implementation is now in put_json() function above

def upload_to_nft_storage(obj: dict) -> str:
    """Upload to NFT.Storage"""
    token = os.getenv('NFT_STORAGE_TOKEN')
    if not token:
        return ""
    
    try:
        json_data = json.dumps(obj, indent=2)
        json_bytes = json_data.encode('utf-8')
        
        files = {
            'file': ('metadata.json', BytesIO(json_bytes), 'application/json')
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.post(
            'https://api.nft.storage/upload',
            headers=headers,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            cid = result.get('value', {}).get('cid')
            if cid:
                return f"ipfs://{cid}"
        
    except Exception:
        pass
    return ""

def upload_to_infura(obj: dict) -> str:
    """Upload to Infura IPFS"""
    project_id = os.getenv('INFURA_PROJECT_ID')
    project_secret = os.getenv('INFURA_PROJECT_SECRET')
    if not project_id:
        return ""
    
    try:
        import base64
        
        auth_string = f"{project_id}:{project_secret or ''}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        json_data = json.dumps(obj, indent=2)
        json_bytes = json_data.encode('utf-8')
        
        files = {
            'file': ('metadata.json', BytesIO(json_bytes), 'application/json')
        }
        
        headers = {
            'Authorization': f'Basic {auth_b64}'
        }
        
        response = requests.post(
            'https://ipfs.infura.io:5001/api/v0/add',
            headers=headers,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            cid = result.get('Hash')
            if cid:
                return f"ipfs://{cid}"
        
    except Exception:
        pass
    return ""

def upload_to_web3storage(obj: dict) -> str:
    """Upload to Web3.Storage/Storacha (legacy support)"""
    token = os.getenv('WEB3STORAGE_TOKEN')
    if not token:
        return ""
    
    endpoints = [
        'https://api.web3.storage/upload',
        'https://up.storacha.network/upload'
    ]
    
    for endpoint in endpoints:
        try:
            json_data = json.dumps(obj, indent=2)
            json_bytes = json_data.encode('utf-8')
            
            files = {
                'file': ('metadata.json', BytesIO(json_bytes), 'application/json')
            }
            
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('cid', '')
                
                if cid:
                    return f"ipfs://{cid}"
                    
        except Exception:
            continue
    
    return ""