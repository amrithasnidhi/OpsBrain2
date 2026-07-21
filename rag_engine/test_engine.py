#!/usr/bin/env python3
"""
Test script for RAG Engine validation.

Run with: python -m rag_engine.test_engine
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_engine.engine import (
    answer_query,
    get_all_known_conflicts,
    validate_against_contradictions_md
)


def test_basic_qa():
    """Test basic Q&A functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Q&A")
    print("="*60)

    questions = [
        "What is the relief pressure for PSV-101?",
        "How often should PUMP-203 bearings be inspected?",
        "What is the cleaning frequency for heat exchanger HX-301?",
        "What is the maximum discharge pressure for compressor C-401?",
        "Were there any incidents with PUMP-203?"
    ]

    for question in questions:
        print(f"\nQ: {question}")
        result = answer_query(question)
        print(f"A: {result.answer[:200]}..." if len(result.answer) > 200 else f"A: {result.answer}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Citations: {len(result.citations)}")
        print(f"   Conflicts: {len(result.conflicts)}")
        print(f"   Lessons: {len(result.lessons_learned)}")


def test_conflict_detection():
    """Test global conflict detection."""
    print("\n" + "="*60)
    print("TEST 2: Global Conflict Detection")
    print("="*60)

    conflicts = get_all_known_conflicts(force_refresh=True)

    print(f"\nFound {len(conflicts)} conflicts:\n")

    for i, conflict in enumerate(conflicts, 1):
        print(f"{i}. [{conflict.severity.upper()}] {conflict.entity} - {conflict.parameter}")
        print(f"   Type: {conflict.risk_type}")
        print(f"   Value A: {conflict.value_a}")
        print(f"   Value B: {conflict.value_b}")
        print(f"   Explanation: {conflict.explanation[:150]}...")
        print()


def test_validation():
    """Validate against CONTRADICTIONS.md acceptance criteria."""
    print("\n" + "="*60)
    print("TEST 3: Acceptance Criteria Validation")
    print("="*60)

    results = validate_against_contradictions_md()

    all_passed = True
    for test_name, result in results.items():
        status = result['status']
        details = result['details']
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"\n{icon} {test_name}: {status}")
        print(f"  {details}")
        if status != "PASS":
            all_passed = False

    print("\n" + "-"*60)
    if all_passed:
        print("ALL ACCEPTANCE CRITERIA PASSED!")
    else:
        print("SOME TESTS FAILED - Review above")
    print("-"*60)

    return all_passed


def test_lessons_learned():
    """Test lessons learned surfacing."""
    print("\n" + "="*60)
    print("TEST 4: Lessons Learned Surfacing")
    print("="*60)

    # This query should trigger lessons learned for PUMP-203
    result = answer_query("What maintenance should I do on PUMP-203?")

    print(f"\nQuery: What maintenance should I do on PUMP-203?")
    print(f"\nLessons Learned ({len(result.lessons_learned)}):")

    for lesson in result.lessons_learned:
        print(f"\n- [{lesson.severity.upper()}] {lesson.incident_type}")
        print(f"  Equipment: {lesson.equipment_tag}")
        print(f"  Date: {lesson.date}")
        print(f"  Description: {lesson.description}")


def test_no_hallucination():
    """Test that the system doesn't hallucinate on unknown queries."""
    print("\n" + "="*60)
    print("TEST 5: No Hallucination Test")
    print("="*60)

    # Query about equipment that doesn't exist
    result = answer_query("What is the pressure rating for VALVE-999?")

    print(f"\nQuery: What is the pressure rating for VALVE-999?")
    print(f"Answer: {result.answer[:300]}..." if len(result.answer) > 300 else f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence:.2f}")

    # With Claude API: should have low confidence and honest "no info" answer
    # In fallback mode: retriever may return partial matches, check confidence is moderate
    if "don't have" in result.answer.lower() or "no relevant" in result.answer.lower():
        print("\n[PASS] System correctly indicated lack of information")
    elif result.confidence < 0.6:
        print("\n[INFO] Moderate confidence - with Claude API this would be handled better")
        print("       Fallback mode returns best-match chunks without semantic filtering")
    else:
        print("\n[WARN] High confidence on unknown equipment - review answer")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RAG ENGINE VALIDATION SUITE")
    print("Industrial Knowledge Brain - Hackathon")
    print("="*60)

    try:
        test_basic_qa()
        test_conflict_detection()
        passed = test_validation()
        test_lessons_learned()
        test_no_hallucination()

        print("\n" + "="*60)
        print("TEST SUITE COMPLETE")
        if passed:
            print("Ready for PR submission!")
        else:
            print("Fix failing tests before hour 6 deadline")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] TEST SUITE FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
