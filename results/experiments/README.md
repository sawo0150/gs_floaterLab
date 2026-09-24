# Immutable legacy experiment artifacts

이 디렉터리의 `expNN*` 경로는 source manifest, runner, 문서가 직접 참조하므로
이동·개명·병합하지 않는다. 사람이 탐색하는 시작점은
`context/experiments/README.md`다.

새 결과는 숫자만 늘리지 않고 다음 구조를 사용한다.

```text
results/campaigns/<campaign>/<question>/<dataset>/<scene>/<arm>/
```

각 run은 기존과 동일하게 command, source lock, runtime JSON, fixed held-out
evaluation을 자체 포함해야 한다. 실패/중단 artifact도 덮어쓰지 않는다.
