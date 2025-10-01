#!/usr/bin/env python3
"""
Backend API Testing Suite for Alumni & Events System
Tests all backend endpoints according to test_result.md requirements
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Use the configured backend URL from frontend .env
BASE_URL = "https://grad-connect-2.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def test_health_endpoint(self):
        """Test GET /api/ health check"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Health Check", True, f"Status: {response.status_code}, Message: {data['message']}")
                    return True
                else:
                    self.log_test("Health Check", False, "Missing 'message' field in response", data)
                    return False
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_auth_login(self):
        """Test POST /api/auth/login"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.auth_token = data["access_token"]
                    self.log_test("Auth Login", True, f"Token received, type: {data.get('token_type', 'unknown')}")
                    return True
                else:
                    self.log_test("Auth Login", False, "Missing token fields in response", data)
                    return False
            else:
                self.log_test("Auth Login", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Auth Login", False, f"Request failed: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_alumni_crud(self):
        """Test Alumni CRUD operations"""
        if not self.auth_token:
            self.log_test("Alumni CRUD", False, "No auth token available")
            return False
        
        # Test GET /api/alumni (should work without auth)
        try:
            response = requests.get(f"{self.base_url}/alumni", timeout=10)
            if response.status_code == 200:
                initial_alumni = response.json()
                self.log_test("Alumni List (Initial)", True, f"Retrieved {len(initial_alumni)} alumni")
            else:
                self.log_test("Alumni List (Initial)", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Alumni List (Initial)", False, f"Request failed: {str(e)}")
            return False
        
        # Test POST /api/alumni (requires auth)
        try:
            alumni_data = {
                "full_name": "Maria Popescu",
                "graduation_year": 2020,
                "bacalaureat_passed": True,
                "path": "employed",
                "email": "maria.popescu@example.com",
                "phone": "+40123456789"
            }
            
            response = requests.post(
                f"{self.base_url}/alumni",
                json=alumni_data,
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                created_alumni = response.json()
                alumni_id = created_alumni.get("id")
                if alumni_id:
                    self.log_test("Alumni Create", True, f"Created alumni with ID: {alumni_id}")
                    
                    # Test GET /api/alumni again to verify it includes the new one
                    response = requests.get(f"{self.base_url}/alumni", timeout=10)
                    if response.status_code == 200:
                        updated_alumni = response.json()
                        if len(updated_alumni) > len(initial_alumni):
                            self.log_test("Alumni List (After Create)", True, f"Now has {len(updated_alumni)} alumni")
                            return True
                        else:
                            self.log_test("Alumni List (After Create)", False, "New alumni not found in list")
                            return False
                    else:
                        self.log_test("Alumni List (After Create)", False, f"Status: {response.status_code}")
                        return False
                else:
                    self.log_test("Alumni Create", False, "No ID in created alumni", created_alumni)
                    return False
            else:
                self.log_test("Alumni Create", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Alumni Create", False, f"Request failed: {str(e)}")
            return False
    
    def test_events_crud(self):
        """Test Events CRUD operations"""
        if not self.auth_token:
            self.log_test("Events CRUD", False, "No auth token available")
            return False
        
        # Test GET /api/events (should work without auth)
        try:
            response = requests.get(f"{self.base_url}/events", timeout=10)
            if response.status_code == 200:
                initial_events = response.json()
                self.log_test("Events List (Initial)", True, f"Retrieved {len(initial_events)} events")
            else:
                self.log_test("Events List (Initial)", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Events List (Initial)", False, f"Request failed: {str(e)}")
            return False
        
        # Test POST /api/events (requires auth)
        try:
            event_data = {
                "title": "Reuniunea Absolvenților 2024",
                "date": "2024-06-15",
                "location": "Aula Magna, Universitatea București",
                "description": "Eveniment anual pentru absolvenții promoției 2020-2024"
            }
            
            response = requests.post(
                f"{self.base_url}/events",
                json=event_data,
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                created_event = response.json()
                event_id = created_event.get("id")
                if event_id:
                    self.log_test("Event Create", True, f"Created event with ID: {event_id}")
                    
                    # Test GET /api/events again to verify it includes the new one
                    response = requests.get(f"{self.base_url}/events", timeout=10)
                    if response.status_code == 200:
                        updated_events = response.json()
                        if len(updated_events) > len(initial_events):
                            self.log_test("Events List (After Create)", True, f"Now has {len(updated_events)} events")
                            return event_id  # Return event ID for invitation testing
                        else:
                            self.log_test("Events List (After Create)", False, "New event not found in list")
                            return False
                    else:
                        self.log_test("Events List (After Create)", False, f"Status: {response.status_code}")
                        return False
                else:
                    self.log_test("Event Create", False, "No ID in created event", created_event)
                    return False
            else:
                self.log_test("Event Create", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Event Create", False, f"Request failed: {str(e)}")
            return False
    
    def test_invitations(self, event_id: str):
        """Test Invitations functionality"""
        if not self.auth_token:
            self.log_test("Invitations", False, "No auth token available")
            return False
        
        if not event_id:
            self.log_test("Invitations", False, "No event ID available")
            return False
        
        # Test POST /api/invitations (requires auth)
        try:
            invitation_data = {
                "event_id": event_id
            }
            
            response = requests.post(
                f"{self.base_url}/invitations",
                json=invitation_data,
                headers=self.get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                created_invitation = response.json()
                invitation_token = created_invitation.get("token")
                if invitation_token:
                    self.log_test("Invitation Create", True, f"Created invitation with token: {invitation_token[:8]}...")
                    
                    # Test GET /api/invitations/{token} (public endpoint)
                    response = requests.get(f"{self.base_url}/invitations/{invitation_token}", timeout=10)
                    if response.status_code == 200:
                        invitation_data = response.json()
                        if "invitation" in invitation_data and "event" in invitation_data:
                            self.log_test("Invitation Fetch", True, "Retrieved invitation with event details")
                            return True
                        else:
                            self.log_test("Invitation Fetch", False, "Missing invitation or event data", invitation_data)
                            return False
                    else:
                        self.log_test("Invitation Fetch", False, f"Status: {response.status_code}", response.text)
                        return False
                else:
                    self.log_test("Invitation Create", False, "No token in created invitation", created_invitation)
                    return False
            else:
                self.log_test("Invitation Create", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Invitations", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print(f"🚀 Starting Backend API Tests")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test 1: Health check
        health_ok = self.test_health_endpoint()
        
        # Test 2: Authentication
        auth_ok = self.test_auth_login()
        
        # Test 3: Alumni CRUD
        alumni_ok = self.test_alumni_crud()
        
        # Test 4: Events CRUD
        event_id = self.test_events_crud()
        events_ok = bool(event_id)
        
        # Test 5: Invitations
        invitations_ok = self.test_invitations(event_id) if event_id else False
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed!")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            return False

def main():
    """Main test execution"""
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()