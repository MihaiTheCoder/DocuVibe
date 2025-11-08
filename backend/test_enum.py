"""Test enum value behavior"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models.processing_job import JobStatus
from app.models.github_integration import IssueStatus

# Test what .value actually returns
print(f"JobStatus.PENDING = {JobStatus.PENDING}")
print(f"JobStatus.PENDING.value = {JobStatus.PENDING.value}")
print(f"type = {type(JobStatus.PENDING.value)}")
print()
print(f"IssueStatus.READY = {IssueStatus.READY}")
print(f"IssueStatus.READY.value = {IssueStatus.READY.value}")
print(f"type = {type(IssueStatus.READY.value)}")
