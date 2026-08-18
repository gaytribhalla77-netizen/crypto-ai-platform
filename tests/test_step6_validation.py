from certification.step6 import offline_step6_passes, run_offline_step6_gates


def test_step6_offline_validation_gates_pass():
    gates = run_offline_step6_gates()
    assert gates
    assert all(g.passed for g in gates), [(g.name, g.detail) for g in gates if not g.passed]
    assert offline_step6_passes()
