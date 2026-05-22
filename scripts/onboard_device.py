#!/usr/bin/env python3
"""
Device onboarding helper — generates QR codes for device registration.
Usage: python scripts/onboard_device.py --name "Soilnode N-02" --type SOILNODE --farm <farm_id>
"""
import argparse
import asyncio
import httpx
import json
import sys

API_URL = "http://localhost:8000"

async def onboard(name: str, device_type: str, farm_id: str, serial: str | None, token: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_URL}/farms/{farm_id}/devices/register",
            json={"name": name, "type": device_type, "serial": serial},
            headers={"Authorization": f"Bearer {token}"},
        )
        if res.status_code != 201:
            print(f"❌ Registration failed: {res.status_code} {res.text}")
            sys.exit(1)

        data = res.json()
        print(f"\n✅ Device registered successfully!")
        print(f"   Name:    {data['name']}")
        print(f"   ID:      {data['id']}")
        print(f"   Type:    {data['type']}")
        print(f"   API Key: {data['api_key']}")
        print(f"\n⚠️  Save this API key now — it will NOT be shown again.\n")
        print(f"   Configure the device with:")
        print(f"   DEVICE_ID={data['id']}")
        print(f"   API_KEY={data['api_key']}")
        print(f"   FARM_ID={farm_id}")
        print(f"   HUB_URL=http://<hub-ip>:8001")

        # Try to print QR code if qrcode library available
        try:
            import qrcode
            config = json.dumps({
                "device_id": data['id'], "api_key": data['api_key'],
                "farm_id": farm_id, "hub_url": "http://hub.local:8001"
            })
            qr = qrcode.QRCode()
            qr.add_data(config)
            qr.make(fit=True)
            print("\n   Scan this QR code with the Famtech provisioning app:\n")
            qr.print_ascii(invert=True)
        except ImportError:
            print("   (Install qrcode library to get a printable QR code)")

def main():
    parser = argparse.ArgumentParser(description="Famtech device onboarding")
    parser.add_argument("--name", required=True)
    parser.add_argument("--type", required=True, choices=["WATCHTOWER","SOILNODE","FEEDER","WORKERTAG","FENCEGRID","HUB","AQUASENSE"])
    parser.add_argument("--farm", required=True, help="Farm ID")
    parser.add_argument("--serial", default=None)
    parser.add_argument("--token", required=True, help="JWT access token")
    args = parser.parse_args()
    asyncio.run(onboard(args.name, args.type, args.farm, args.serial, args.token))

if __name__ == "__main__":
    main()
