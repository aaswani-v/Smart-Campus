"""
Smart Campus - Biometric Verification Service
Simulated fingerprint and RFID verification for attendance
"""

import hashlib
import secrets
import os
from typing import Dict, Optional
from datetime import datetime


class BiometricService:
    """Simulated biometric verification (fingerprint + RFID)"""
    
    def __init__(self):
        # In a real system, these would connect to hardware APIs
        self.fingerprint_templates: Dict[str, str] = {}
        self.rfid_tags: Dict[str, str] = {}
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load biometric mappings from database on init"""
        # This would query the database in production
        pass
    
    def generate_fingerprint_hash(self, raw_data: str = None) -> str:
        """
        Generate a fingerprint hash
        In production: This would process actual fingerprint scanner data
        For demo: Generates a simulated hash
        """
        if raw_data:
            # Hash the provided data
            data = raw_data.encode('utf-8')
        else:
            # Generate random fingerprint simulation
            data = secrets.token_bytes(32)
        
        return hashlib.sha256(data).hexdigest()
    
    def generate_rfid_tag(self) -> str:
        """
        Generate an RFID tag ID
        In production: Would read from actual RFID scanner
        For demo: Generates a 32-char hex tag
        """
        return secrets.token_hex(16).upper()
    
    def register_fingerprint(self, student_id: str, fingerprint_data: str = None) -> Dict:
        """
        Register a student's fingerprint
        Returns the fingerprint hash to store in database
        """
        fingerprint_hash = self.generate_fingerprint_hash(fingerprint_data)
        self.fingerprint_templates[student_id] = fingerprint_hash
        
        return {
            'success': True,
            'student_id': student_id,
            'fingerprint_hash': fingerprint_hash,
            'registered_at': datetime.utcnow().isoformat()
        }
    
    def register_rfid(self, student_id: str, rfid_tag: str = None) -> Dict:
        """
        Register a student's RFID card
        Returns the RFID tag to store in database
        """
        if not rfid_tag:
            rfid_tag = self.generate_rfid_tag()
        
        self.rfid_tags[student_id] = rfid_tag
        
        return {
            'success': True,
            'student_id': student_id,
            'rfid_tag': rfid_tag,
            'registered_at': datetime.utcnow().isoformat()
        }
    
    def verify_fingerprint(self, student_id: str, provided_hash: str, stored_hash: str) -> Dict:
        """
        Verify a fingerprint against stored template
        In production: Would compare actual biometric templates
        For demo: Compares hashes
        """
        is_match = provided_hash == stored_hash
        
        # Simulate a confidence score
        confidence = 95.0 if is_match else 0.0
        
        return {
            'verified': is_match,
            'student_id': student_id,
            'confidence': confidence,
            'method': 'fingerprint',
            'verified_at': datetime.utcnow().isoformat()
        }
    
    def verify_rfid(self, student_id: str, provided_tag: str, stored_tag: str) -> Dict:
        """
        Verify an RFID tag
        In production: Would read from hardware scanner
        """
        is_match = provided_tag.upper() == stored_tag.upper()
        
        return {
            'verified': is_match,
            'student_id': student_id,
            'confidence': 100.0 if is_match else 0.0,
            'method': 'rfid',
            'verified_at': datetime.utcnow().isoformat()
        }
    
    def simulate_fingerprint_scan(self, student_id: str) -> Dict:
        """
        Simulate a fingerprint scan for demo purposes
        Returns a hash that can be verified against stored data
        """
        # In demo mode, return the stored hash (guaranteed match)
        if student_id in self.fingerprint_templates:
            return {
                'scanned': True,
                'hash': self.fingerprint_templates[student_id],
                'quality': 95.0
            }
        
        # If not registered, return random hash (won't match)
        return {
            'scanned': True,
            'hash': self.generate_fingerprint_hash(),
            'quality': 90.0
        }
    
    def simulate_rfid_tap(self, student_id: str) -> Dict:
        """
        Simulate an RFID card tap for demo purposes
        """
        if student_id in self.rfid_tags:
            return {
                'tapped': True,
                'tag': self.rfid_tags[student_id]
            }
        
        return {
            'tapped': True,
            'tag': self.generate_rfid_tag()
        }
    
    def multi_factor_verify(
        self,
        student_id: str,
        face_verified: bool = False,
        face_confidence: float = 0.0,
        fingerprint_hash: str = None,
        stored_fingerprint: str = None,
        rfid_tag: str = None,
        stored_rfid: str = None
    ) -> Dict:
        """
        Perform multi-factor biometric verification
        Requires at least 2 factors to pass
        """
        factors = []
        total_score = 0.0
        
        # Face verification
        if face_verified and face_confidence >= 70:
            factors.append({
                'method': 'face',
                'verified': True,
                'confidence': face_confidence
            })
            total_score += face_confidence
        else:
            factors.append({
                'method': 'face',
                'verified': False,
                'confidence': face_confidence
            })
        
        # Fingerprint verification
        if fingerprint_hash and stored_fingerprint:
            fp_result = self.verify_fingerprint(student_id, fingerprint_hash, stored_fingerprint)
            factors.append({
                'method': 'fingerprint',
                'verified': fp_result['verified'],
                'confidence': fp_result['confidence']
            })
            if fp_result['verified']:
                total_score += fp_result['confidence']
        
        # RFID verification
        if rfid_tag and stored_rfid:
            rfid_result = self.verify_rfid(student_id, rfid_tag, stored_rfid)
            factors.append({
                'method': 'rfid',
                'verified': rfid_result['verified'],
                'confidence': rfid_result['confidence']
            })
            if rfid_result['verified']:
                total_score += rfid_result['confidence']
        
        # Count passed factors
        passed_factors = sum(1 for f in factors if f['verified'])
        
        # Calculate overall confidence
        if passed_factors > 0:
            avg_confidence = total_score / passed_factors
        else:
            avg_confidence = 0.0
        
        # At least 2 factors required
        is_valid = passed_factors >= 2
        
        return {
            'student_id': student_id,
            'is_valid': is_valid,
            'factors_passed': passed_factors,
            'total_factors': len(factors),
            'factors': factors,
            'average_confidence': avg_confidence,
            'verified_at': datetime.utcnow().isoformat()
        }


# Singleton instance
_biometric_service = None

def get_biometric_service() -> BiometricService:
    """Get singleton BiometricService instance"""
    global _biometric_service
    if _biometric_service is None:
        _biometric_service = BiometricService()
    return _biometric_service
