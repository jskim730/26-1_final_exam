# Phase-Conditioned Diffusion Policy — 최종 발표 PPT 구성 초안

> 이 문서는 **PPT 본체가 아니라**, "어느 슬라이드에 무엇을 서술/시각화할지"를 정한 **흐름·페이지 분배 설계도**입니다.
> 각 슬라이드는 ① 핵심 메시지 ② 서술할 내용 ③ 시각자료(저장소 figure 매핑) ④ 발표 노트 순으로 정리했습니다.
> 논문 흐름(Intro → Background → Method → Experiments → Results → Discussion → Conclusion)을 따르되, **AI + X(현실 문제)** 와 **proposal 이후 발전 과정**을 명시적으로 녹였습니다.

---

## 0. 전체 분량 분배 (총 36슬라이드)

| 파트 | 섹션 | 슬라이드 | 누적 | 비중 |
|---|---|---|---|---|
| A | 표지 & 개요 | 1–2 | 2 | 6% |
| **B** | **Introduction (AI + X / 현실 문제 — 교수님 강조점)** | **3–8** | **8** | **17%** |
| C | Background & Related Work | 9–11 | 11 | 8% |
| **D** | **Proposal → Final: 연구의 발전 과정** | **12–14** | **14** | **8%** |
| E | Method | 15–22 | 22 | 22% |
| F | Experiments & Protocol | 23–25 | 25 | 8% |
| **G** | **Results** | **26–32** | **32** | **19%** |
| H | Discussion & Conclusion | 33–36 | 36 | 11% |

**분량 설계 의도**
- Introduction(파트 B)에 6슬라이드를 배정 — 교수님이 "생성 모델이 현실 문제를 어떻게 푸는가(AI+X)"를 중시하시므로, 여기서 novelty와 현실 문제의 유사성을 충분히 펼침.
- Method(파트 E)와 Results(파트 G)가 본문의 두 축. 논문처럼 "주장(contribution) → 증거(figure/table)" 대응이 한눈에 보이게 배치.
- Proposal→Final 발전 과정(파트 D)을 독립 섹션으로 빼서, "제안서 이후 무엇을 어떻게 발전시켰는지"를 평가자가 즉시 인지하도록 함.

**관통하는 한 줄 서사 (deck 전체의 spine)**
> "다리 달린 로봇은 본질적으로 *여러 개의 정답(gait)* 을 가진다 → 평균내는 결정적 모델은 무너진다 → 생성 모델(Diffusion Policy)이 답이다 → 하지만 이 분야의 핵심 inductive bias인 *phase* 를 안 쓴다 → 우리는 phase **trajectory** 를 condition으로 주입하고, frozen estimator의 sync loss로 *명령한 리듬을 따르는 controllable locomotion* 을 생성한다."

---

# 파트 A — 표지 & 개요

## Slide 1 — Title
- **핵심 메시지**: 프로젝트 정체성을 한 화면에.
- **서술할 내용**
  - 제목: *Phase-Conditioned Diffusion Policy for Quadruped Locomotion*
  - 부제(AI+X 명시): *생성 모델로 "명령 가능한 보행 리듬"을 만들다 — Generative Models × Legged Locomotion*
  - 팀명/팀원 이름·학번, 과목명, 날짜
  - 한 줄 tagline: *"분야의 inductive bias(phase)를 generative framework 안으로"*
- **시각자료**: Ant rollout 스크린샷 또는 영상 첫 프레임 1컷(가능하면 실제 보행 영상 thumbnail), 배경은 단색.
- **발표 노트**: 30초. 제목과 "controllable locomotion" 키워드만 각인.

## Slide 2 — 발표 흐름 (Roadmap)
- **핵심 메시지**: 청중에게 30분의 지도를 먼저 준다.
- **서술할 내용**
  - 7개 챕터를 한 줄씩: 현실 문제 → 배경 → proposal 이후 발전 → 방법(4-model) → 실험 설계 → 결과 → 결론
  - 하단에 "오늘의 핵심 주장 4가지"를 미리 1줄로 예고(품질 보존 / 주파수 제어 / OOD 일반화 / phase 동기화)
- **시각자료**: 좌→우 화살표 7단계 흐름도. 본문 진행 시 현재 위치 하이라이트하는 progress bar로 재활용 가능.
- **발표 노트**: 20초. "오늘은 *논문 한 편*을 발표한다"는 톤 설정.

---

# 파트 B — Introduction (AI + X / 현실 문제) ★교수님 강조점 집중

> 이 파트의 목표: **(1) 현실의 진짜 문제를 생생하게 제시하고, (2) 왜 *생성 모델*이 그 문제의 해법인지, (3) 우리의 novelty(phase trajectory conditioning)가 현실 제어 문제와 어떻게 닮았는지**를 설득. 기술 디테일은 최소화하고 "왜 이게 중요한가"에 집중.

## Slide 3 — 현실 문제: 다리 달린 로봇은 왜 어려운가 (Hook)
- **핵심 메시지**: Physical AI가 디지털을 넘어 물리 세계로 왔고, 그 최전선이 legged locomotion이다.
- **서술할 내용**
  - 실사용 사례: Boston Dynamics Spot, Unitree Go2, ANYmal, Tesla Optimus 등 — "AI가 물리 세계에서 *걷고* 있다"
  - 현실 요구사항: 지형 적응(계단·자갈·빙판), 에너지 효율, 명령 추종(속도·리듬 변경). 즉 로봇은 *하나의 정해진 걸음*이 아니라 *상황에 맞게 보행을 조절*해야 한다.
  - 문제 제기 한 줄: *"어떻게 하면 데이터로부터, 명령에 따라 리듬을 바꿀 수 있는 보행 정책을 학습할까?"*
- **시각자료**: 실제 4족 로봇 사진 3~4컷 콜라주(출처 표기). 가능하면 "다양한 gait(walk/trot/gallop)" 동물 일러스트 1컷.
- **발표 노트**: 여기서 청중을 "현실 문제"에 묶어두는 게 핵심. 기술 용어 X.

## Slide 4 — 핵심 난제: 보행의 multimodality ("평균은 정답이 아니다")
- **핵심 메시지**: 같은 상황에서 *합리적인 보행이 여러 개* 존재한다 → 결정적 모델은 평균내어 무너진다.
- **서술할 내용**
  - 직관 예시(proposal의 hook 재사용): manipulation의 T자 밀기 — 왼쪽으로/오른쪽으로 둘 다 정답인데, 평균(직진)은 실패.
  - 보행으로 전이: 같은 전진 속도 명령에도 walk vs trot vs gallop 등 여러 자연스러운 gait 존재. 이를 평균내면 *어느 것도 아닌 어색한 동작*.
  - 결론: *behavior cloning(모방학습)의 multimodality 문제* → "분포 자체를 학습해야 한다".
- **시각자료**: T자 예시 손그림(왼/오/평균=실패) + 그 아래 보행 버전(여러 gait → 평균 실패) 대응 도식.
- **발표 노트**: 이 슬라이드가 "왜 생성 모델인가"의 논리적 사전 정지작업.

## Slide 5 — 왜 생성 모델인가: Diffusion Policy의 등장
- **핵심 메시지**: 분포를 학습하는 생성 모델이 multimodality 문제의 답이고, 그 대표가 Diffusion Policy다.
- **서술할 내용**
  - Diffusion Policy (Chi et al., RSS 2023): noise → 점진적 denoising → action chunk 생성. manipulation에서 BC의 multimodality를 해결한 새 표준.
  - 두 가지 구조적 강점만 강조: ① **chunk 단위 예측**(한 번에 H step 동시 생성) ② **conditional 생성**(observation을 조건으로). 이 둘이 뒤에서 우리 novelty의 토대가 됨을 예고.
  - 한 줄: *"같은 상황의 여러 정답을 *분포*로 표현 → 생성 모델의 본질적 강점이 보행에서 빛난다."*
- **시각자료**: Diffusion Policy 원 논문 architecture diagram(인용 표기) 또는 noise→action chunk denoising 모식도.
- **발표 노트**: "왜 RL이 아니라 생성 모델?"이라는 질문을 선제적으로 해소.

## Slide 6 — 보행의 본질: phase라는 inductive bias
- **핵심 메시지**: 보행은 본질적으로 주기 운동이고, 이 분야 30년의 합의가 *phase*다.
- **서술할 내용**
  - Quadruped는 본질적으로 주기 운동(한 cycle: 0→π/2→π→3π/2→2π). trot은 대각선 다리쌍이 번갈아 swing.
  - 분야의 모든 주요 방법론(MPC, model-free RL)이 phase를 **명시적으로** 정책에 주입 → phase는 보행 제어의 핵심 inductive bias.
  - 그런데: Diffusion Policy는 *manipulation(주기성 없음)* 에서 출발 → **phase라는 inductive bias를 미보유**.
- **시각자료**: 4족 trotting phase 도식(다리쌍 swing/stance 타이밍 다이어그램) + 한 cycle 위상 표기. (가능하면 Ant 관절 신호에서 추출한 실제 phase 곡선 1컷 — `figures/data_phase_advance.png` 미리보기로 연결 가능)
- **발표 노트**: 여기서 "gap"의 절반(phase의 중요성)을 세움.

## Slide 7 — Gap & 우리의 Novelty: phase를 generative framework 안으로 (AI + X 위치)
- **핵심 메시지**: 두 세계(생성 모델 ↔ 보행의 phase)가 만나는 빈틈이 우리 자리다. 그리고 그 novelty는 현실 제어 문제와 직접 닮았다.
- **서술할 내용**
  - 세 흐름의 교차점으로 위치 선정: ① Diffusion Policy의 강점(multimodality) ② 보행의 핵심 정보(phase) ③ 둘 사이 gap(DP는 phase를 안 씀).
  - **우리의 novelty 한 줄**: *단일 phase 값이 아니라, action chunk 전체에 대응하는 phase **trajectory** (φ_t … φ_{t+H-1})를 condition으로 주입* → sampling 시점에 "이 chunk를 어느 리듬으로 진행할지"가 제어 가능.
  - **현실 문제와의 유사성(여기를 강조)**:
    - 지휘자가 템포를 지시하듯 / 크루즈 컨트롤이 속도를 잡듯, 우리는 **로봇의 보행 리듬(주파수)을 명령**한다.
    - 현실 가치: 거친 지형엔 느리고 신중한 스텝, 평지엔 빠른 스텝 — *명령으로 gait 리듬을 modulate* 하는 능력은 에너지 효율·지형 적응의 핵심. 기존 diffusion policy는 *모방만* 할 뿐 리듬을 명령받지 못함 → 우리가 그 "제어 손잡이"를 만든다.
  - 그래서 이건 단순 기법이 아니라 *AI(생성 모델) + X(legged locomotion 제어)* 의 구체적 해법.
- **시각자료**: 벤다이어그램(생성 모델 ∩ 보행 phase = 우리 연구) + 우측에 "현실 비유" 아이콘 3개(지휘자/크루즈컨트롤/지형적응).
- **발표 노트**: 교수님 평가 포인트가 집중되는 슬라이드. "novelty ↔ 현실 문제" 연결을 말로 한 번 더 또렷이.

## Slide 8 — Research Question & Contributions (Preview)
- **핵심 메시지**: 한 문장의 질문과, 오늘 증명할 4개 주장.
- **서술할 내용**
  - Research Question: *"보행의 핵심 inductive bias인 phase를 diffusion policy에 어떻게 결합하면, *명령한 리듬을 따르는* controllable locomotion을 생성할 수 있는가?"*
  - Contributions(뒤 결과 슬라이드와 1:1 대응 예고):
    1. **품질 보존/향상** — phase trajectory conditioning이 vanilla 대비 더 나은 실보행 정책 학습
    2. **주파수 제어성(controllability)** — in-dist에서 |freq err| < 0.06 Hz, PLV > 0.88; periodic의 mode collapse 회피
    3. **우아한 일반화(graceful generalization)** — 느린 OOD에서 zero-shot tracking, 빠른 OOD에서 graceful degradation
    4. **frozen estimator를 통한 phase 동기화(ours)** — sync loss(λ=0.12) fine-tune로 품질·추종 동시 추가 향상
- **시각자료**: 4개 contribution 카드(아이콘+한 줄). 각 카드에 "→ Slide 26/27/28/29" 식 미리보기 라벨.
- **발표 노트**: 이 4개가 "오늘의 약속". Results에서 그대로 회수.

---

# 파트 C — Background & Related Work

## Slide 9 — Diffusion Policy 동작 원리 (Base 방법론)
- **핵심 메시지**: 우리 base를 1분 안에 이해시킨다.
- **서술할 내용**
  - DDPM 기반: forward(noise 추가) ↔ reverse(denoising). 정책 학습에선 action chunk를 denoising target으로.
  - 우리 설정 수치(나중 Method에서 재확인): DDPM train timesteps 100, DDIM inference 16 steps, β-schedule `squaredcos_cap_v2`, **ε-prediction**, EMA 사용.
  - conditional 1D U-Net이 backbone: observation window를 global condition으로 받아 다음 action chunk 생성.
- **시각자료**: noise→denoise→action chunk 파이프라인 모식도 + U-Net 블록 간단 도식.
- **발표 노트**: 수식은 ε-prediction 1줄만. 깊은 유도는 appendix로.

## Slide 10 — Phase & Gait, 그리고 Hilbert Transform
- **핵심 메시지**: 데이터에서 phase를 *사후(post-hoc)* 로 어떻게 얻는지.
- **서술할 내용**
  - phase φ ∈ [0, 2π): 보행 주기 내 위치. (cos φ, sin φ)로 인코딩해 경계 불연속 제거.
  - Hilbert transform 직관: 신호를 −90° 위상 이동 → analytic signal 구성 → 순간 위상(instantaneous phase)을 atan2로 추출.
  - 적용: Ant의 **hip joint** 신호에 Hilbert transform → 각 시점의 phase 라벨 부여(데모는 학습 후 라벨링이 아니라, 수집된 데모에 post-hoc 라벨링).
- **시각자료**: hip joint 신호 곡선 + 그 위에 추출된 phase 곡선 오버레이(`figures/data_phase_advance.png` 활용).
- **발표 노트**: "phase는 학습으로 만든 게 아니라 *신호에서 측정한 것*"임을 분명히 — 평가의 정직성 포인트.

## Slide 11 — Related Work: Phase-Aware RL (PAPL) & Positioning
- **핵심 메시지**: 가장 가까운 선행연구는 phase의 중요성을 입증했지만 *RL* 이다 — 우리는 *생성 모델* 로 그 자리를 채운다.
- **서술할 내용**
  - PAPL (Yoon et al., 2026, KAIST): quadruped 제어에서 phase가 핵심임을 검증. 단, RL 기반(생성 모델 아님) → multimodality·controllable generation 관점은 다룸이 없음.
  - 우리 positioning 한 줄: *"phase의 중요성(RL이 입증) × diffusion policy의 강점(생성)을 결합한 첫 시도."*
- **시각자료**: **2×2 positioning table** —
  - 행: phase 사용 O / X, 열: 방법론 RL / Generative
  - 칸: (RL+phase = PAPL 등) / (Generative, no phase = vanilla DP) / **(Generative + phase = Ours, 빈칸을 우리가 채움, 강조색)**
- **발표 노트**: "우리가 메우는 빈칸"을 시각적으로 각인.

---

# 파트 D — Proposal → Final: 연구의 발전 과정 ★"제안 이후 어떻게 발전시켰나"

> 평가자가 "제안서 → 최종" 사이의 *연구적 성장*을 즉시 인지하도록 독립 섹션으로 구성.

## Slide 12 — Proposal에서 제안했던 것 (출발점)
- **핵심 메시지**: 처음엔 3개의 sub-contribution을 제안했다.
- **서술할 내용**
  - (1) **Periodic Phase Encoding** — phase를 Fourier feature(sin φ, cos φ, sin 2φ, …)로 인코딩.
  - (2) **Phase Trajectory Conditioning** — *주 contribution*. 단일 phase가 아닌 chunk 전체 phase trajectory를 condition으로.
  - (3) **Phase-Consistent Sampling** — sampling 시 cost gradient로 생성 action이 주어진 phase trajectory에 동기화되도록 강제(추론 시점 enforcement).
  - 당시 목표: "학습 시 conditioning + 추론 시 enforcement, 두 채널로 phase를 다룬다."
- **시각자료**: 3개 sub-contribution을 좌측 타임라인 형태로. (다음 슬라이드에서 ②는 유지/심화, ①은 단순화, ③은 교체됨을 보일 준비)
- **발표 노트**: "이게 시작점이었다"는 톤. 결과적 변화는 다음 장.

## Slide 13 — 무엇이 바뀌었고, 왜 바뀌었나 (정직한 발전 서사)
- **핵심 메시지**: 실제로 부딪히며 더 단단한 설계로 진화시켰다.
- **서술할 내용 (3개 pivot)**
  - **데이터 파이프라인 pivot**: 정현파+PD, PPO PhaseAwareWrapper, HalfCheetah 사전학습 등 여러 시도 실패 → 최종 **Minari/D4RL Ant 데이터 + Hilbert 사후 phase 라벨링 + 품질 필터링**으로 안착.
  - **multi-frequency → single-frequency 정직한 재정의**: 확보 데이터의 frequency window가 좁음(평균 f̄ ≈ 2.023 Hz, 대략 [1.80, 2.30] Hz) → "다주파수 일반화"는 과장 없이 *future work* 로 명시하고, 학습 분포 내 controllability + OOD 거동에 집중.
  - **sub-contribution ③ 교체 (핵심)**: 추론 시점 Phase-Consistent Sampling은 phase별 K(φ) lookup으로 *offline cost 67% 감소*를 보였으나, rollout이 **seed 분산이 커서 결론 불가** → archive. 대신 **학습 시점**의 해법으로 전환: **frozen phase estimator의 sync loss** 로 fine-tune (= 최종 ours).
- **시각자료**: 좌(Proposal 3개) → 우(Final) 화살표 매핑 다이어그램. ②=심화(굵게), ①=단순화, ③=교체(점선→실선으로 "training-time"으로 이동).
- **발표 노트**: "실패를 정직하게 학습으로 전환"이 이 연구의 성숙도. 교수님이 좋아할 메타 포인트.

## Slide 14 — 최종 연구 설계: 4-Model Progressive Ablation
- **핵심 메시지**: 발전의 결론은 "단계적으로 phase 정보를 더해가는 4-model 비교".
- **서술할 내용**
  - 단계적 설계로 *각 요소의 기여를 분리 측정*: Vanilla → Periodic → Trajectory → Trajectory+Sync(ours).
  - 이 4개가 곧 Method(파트 E)와 Results(파트 G)의 공통 축임을 선언.
- **시각자료**: 4-model 사다리(아래에서 위로 phase 정보가 누적되는 계단 도식). ours를 최상단 빨강 강조.
- **발표 노트**: "지금부터 이 4개를 하나씩 본다"로 Method 진입.

---

# 파트 E — Method

## Slide 15 — 전체 방법 개요 (Method Spine)
- **핵심 메시지**: 데이터 → 4개 모델 → 평가의 전체 그림 한 장.
- **서술할 내용**
  - 파이프라인: 데이터 준비(01) → Vanilla(02) → Periodic(03) → Trajectory(04) → Frozen estimator+Sync(05) → 통합 평가(06).
  - 4개 모델이 *동일 Dataset/training loop* 를 공유하고, condition function만 교체된다는 점(공정 비교 보장).
- **시각자료**: 노트북 01→06 흐름도(README의 실행 흐름 재구성). 각 단계 산출물(checkpoint/figure) 라벨.
- **발표 노트**: "모든 비교가 같은 토대 위"라는 공정성 강조.

## Slide 16 — 데이터 파이프라인
- **핵심 메시지**: phase-coherent 데모를 어떻게 추출·정제했나.
- **서술할 내용**
  - Minari Ant dataset(PPO expert)에서 episode 추출 → **Hilbert transform** 으로 hip joint에서 phase 추출 → **품질 필터링**(monotonicity ≥ 0.90, peak sharpness, freq stability ≤ 0.65) → 고품질 데모 선별.
  - train/val split + **train-only normalization stats** 저장(누수 방지). windowing: `obs_horizon=2`, `pred_horizon=16` (obs window → action chunk → phase chunk 동시 인덱싱).
  - 데이터 평균 frequency f̄ ≈ 2.023 Hz (이후 in-dist 기준점).
- **시각자료**: ① 품질 분포 히스토그램 `figures/data_quality_distribution.png` ② 데모 예시 `figures/data_demo_examples.png` ③ phase 추출 `figures/data_phase_advance.png` — 3컷 가로 배치.
- **발표 노트**: 필터링 임계값은 "정직한 데이터 품질 관리"의 증거.

## Slide 17 — Model 1: Vanilla Diffusion Policy (Baseline)
- **핵심 메시지**: phase 없는 기준선.
- **서술할 내용**
  - conditional 1D U-Net이 *observation window만* global condition으로 받아 action chunk denoising.
  - 학습 설정: 60 epoch, batch 256, AdamW(lr 1e-4), cosine LR + warmup, EMA.
  - 역할: 이후 모든 향상의 비교 기준.
- **시각자료**: vanilla 구조 도식 + loss curve `figures/vanilla_dp_loss.png`(작게).
- **발표 노트**: "여기엔 phase가 전혀 없다"를 명확히 — 대조의 출발.

## Slide 18 — Model 2: Periodic Phase Conditioning
- **핵심 메시지**: 가장 단순하게 phase를 한 번 넣어본다.
- **서술할 내용**
  - action chunk의 *첫 phase* φ₀를 (cos φ₀, sin φ₀)로 인코딩해 **global condition에 concat**.
  - (proposal의 Fourier 다항 인코딩을 최종적으로 single (cos, sin) per-chunk로 단순화.)
  - 예고: 이 방식은 sampling 시점 controllability가 약하고 mode collapse 경향(→ Results에서 정량 확인).
- **시각자료**: global condition에 (cos φ₀, sin φ₀)가 붙는 도식.
- **발표 노트**: "단일 phase로는 부족하다"는 다음 단계의 동기 부여.

## Slide 19 — Model 3: Phase Trajectory Conditioning ★주 contribution
- **핵심 메시지**: chunk *전체* phase trajectory를 step별로 주입한다 — 이 연구의 심장.
- **서술할 내용**
  - action chunk 전체 phase trajectory φ_{0:H}를 step별 (cos φ_t, sin φ_t)로 인코딩.
  - U-Net residual block에 **per-step FiLM** 으로 주입 → "각 시점마다 어느 위상이어야 하는지"를 모델 내부에 직접 전달.
  - 이로써 sampling 시 *target phase trajectory(=원하는 리듬)* 를 바꿔 넣으면 controllable generation 가능 → 우리 novelty의 실체.
- **시각자료**: phase trajectory가 U-Net의 각 step에 FiLM으로 들어가는 핵심 다이어그램(이 deck에서 가장 공들일 그림). + 민감도 시각화 `figures/phase_trajectory_sensitivity.png`.
- **발표 노트**: Slide 7의 "지휘자/리듬 명령" 비유를 여기서 회수("그 손잡이가 바로 이 trajectory 주입").

## Slide 20 — Phase Trajectory 구조 디테일 (FiLM 메커니즘)
- **핵심 메시지**: "어떻게 안정적으로" 주입하는가의 엔지니어링.
- **서술할 내용**
  - **Dual condition branch**: ① global observation context ② per-step phase trajectory.
  - **zero-initialized per-step encoder(delta-scale)**: 학습 초기 phase 주입이 0에서 출발 → vanilla로부터 안정적으로 분기(훈련 안정성).
  - pyramid downsampling으로 multi-scale에서 phase 반영.
- **시각자료**: U-Net 단면도 + FiLM (γ, β) 적용 위치, zero-init 화살표 표시.
- **발표 노트**: 청중이 senior 학부생이므로 FiLM = feature-wise affine modulation 한 줄 정의 포함.

## Slide 21 — Model 4: Phase Trajectory + Sync Loss (Ours)
- **핵심 메시지**: 학습된 모델을 frozen estimator로 "리듬에 맞춰" 미세조정한다.
- **서술할 내용**
  - **Frozen Phase Estimator (MLP)**: (obs + action) → phase 예측. 별도로 40 epoch 학습 후 **freeze**.
  - 이 estimator로 생성 action의 phase를 추정하고, 명령 phase와의 **circular sync loss** L_phase 계산.
  - 최종 목표: **L_total = L_diffusion + 0.12 · L_phase**, Phase Trajectory 모델을 ~10–15 epoch fine-tune(lr 5e-5, phase warmup 1 epoch).
- **시각자료**: [생성 action] → [frozen MLP] → [추정 phase] ↔ [명령 phase] 비교 → L_phase 합산 도식. + estimator 학습 곡선 `figures/frozen_phase_estimator_training.png`.
- **발표 노트**: "frozen" 강조 — estimator는 *고정된 측정자* 역할(학습 신호 안정성).

## Slide 22 — Sync Loss 설계 근거 (왜 추론 enforcement가 아니라 학습 loss인가)
- **핵심 메시지**: proposal의 ③(추론 시점)을 학습 시점으로 옮긴 *이유*를 정면으로 설명.
- **서술할 내용**
  - 추론 시점 Phase-Consistent Sampling: offline에선 효과(cost 67%↓)지만 rollout seed 분산이 커 결론 불가 + 추론 비용↑.
  - 학습 시점 sync loss: 한 번 학습되면 추론은 그대로(추가 비용 0), 그리고 정책 가중치에 phase 정합이 내재화 → 더 안정적이고 재현 가능.
  - 메시지: *"같은 목표(phase 동기화)를, 더 안정적인 위치(학습)에서 달성하도록 발전시켰다."*
- **시각자료**: 좌(추론 enforcement: 매 sampling마다 비용+분산) vs 우(학습 sync: 1회 학습, 추론 무비용) 대비 표.
- **발표 노트**: 파트 D의 "발전 서사"와 메아리치게 — 일관된 스토리.

---

# 파트 F — Experiments & Protocol

## Slide 23 — 평가 프로토콜 개요
- **핵심 메시지**: 두 관점으로 공정하게 측정한다.
- **서술할 내용**
  - **Table 1 (In-distribution quality)**: f̄에서 4개 모델 전부 — survival, reward/step, x-velocity, measured frequency. (n_seeds=20, max_steps=1000, 95% CI)
  - **Table 2 (Frequency controllability sweep)**: 3개 phase 모델(vanilla 제외) — 5개 target frequency 명령 후 추종 측정. (n_seeds=10)
  - 동일 rollout protocol·동일 정규화 → 비교 공정성.
- **시각자료**: 좌(Table1: 4모델·품질) / 우(Table2: 3모델·제어) 2분할 카드. seed/step/CI 수치 박스.
- **발표 노트**: "재현성을 위해 seed를 충분히 썼다"를 명시(이후 limitation의 seed 분산 논의와 연결).

## Slide 24 — 평가 지표 (특히 PLV)
- **핵심 메시지**: "주파수가 맞다"와 "위상이 맞다"는 다르다.
- **서술할 내용**
  - **Measured frequency f̂**: unwrapped phase의 선형회귀 기울기 ÷ 2π.
  - **|freq error| = |f̂ − f_cmd|**: 평균 주파수 추종 오차.
  - **PLV (Phase Locking Value)** = |⟨exp(i·Δφ_t)⟩|, Δφ_t = wrap(φ̂(t) − φ_cmd(t)). 범위 [0,1]: 1=완벽한 위상 동기, 0=무관. **주파수가 같아도 위상이 drift하면 PLV는 낮다** — 그래서 controllability의 진짜 척도.
- **시각자료**: 단위원 위 phase error 점들이 뭉치면 PLV↑ / 흩어지면 PLV↓ 모식도. freq만 맞고 위상 drift하는 반례 그림.
- **발표 노트**: PLV 직관이 Results 해석의 열쇠 — 여기서 확실히.

## Slide 25 — Frequency Sweep Grid (In-dist + OOD)
- **핵심 메시지**: 학습 분포 안/밖을 체계적으로 나눠 명령한다.
- **서술할 내용**
  - in-dist 3점: q25, q50(≈ f̄), q75 (학습 window 내부).
  - OOD 2점: q25 − 1.5·IQR (느림), q75 + 1.5·IQR (빠름) — Tukey-style outer fence.
  - 이 grid로 "내부 추종"과 "외삽(extrapolation) 거동"을 동시에 본다.
- **시각자료**: 수직선 위 5개 명령 주파수 점(in-dist 3 / OOD-low / OOD-high), 학습 window 음영.
- **발표 노트**: Slide 28(graceful generalization)의 사전 설정.

---

# 파트 G — Results

> 파트 B Slide 8에서 약속한 contribution 4개를 결과로 회수. 각 슬라이드 = 1개 주장 + 1개 증거.

## Slide 26 — Result 1: In-distribution Gait Quality (Table 1)
- **핵심 메시지**: phase trajectory는 *실보행 품질 자체* 를 끌어올린다.
- **서술할 내용**
  - reward/step: Vanilla 0.979 → Periodic 0.854 → **Trajectory 1.623** → Sync 1.488.
  - x-velocity도 동일 경향(Trajectory 1.247, Sync 1.106 vs Vanilla 0.466). measured freq도 학습 f̄(≈2.0)에 근접.
  - 해석: 단일 phase(Periodic)는 오히려 손해, *trajectory* 부터 큰 도약. (정량 수치는 95% CI 동반)
- **시각자료**: `eval_figure1_reward_per_step_comparison.png`(4모델 bar) + Table 1 요약표. ours 빨강 강조.
- **발표 노트**: "phase 정보를 *충분히* 줘야 품질이 산다"는 메시지.

## Slide 27 — Result 2: Frequency Controllability (Table 2)
- **핵심 메시지**: 명령한 리듬을 실제로 따라간다 — 그리고 sync가 최고.
- **서술할 내용**
  - |freq err|: Periodic 0.713 → Trajectory 0.135 → **Sync 0.035**. PLV: 0.280 → 0.778 → **0.912**.
  - Periodic은 명령과 무관하게 평탄(mode collapse) → controllability 사실상 없음. Trajectory가 추종을 열고, **Sync가 위상 정합까지 끌어올림**.
- **시각자료**: `eval_figure3_target_vs_measured_freq.png`(command vs measured 산점도 + 완벽추종 대각선). 보조로 `eval_figure2_reward_per_step_vs_freq.png`.
- **발표 노트**: 산점도에서 ours 점들이 대각선에 밀착함을 손으로 짚기.

## Slide 28 — Result 3: Graceful Generalization (OOD)
- **핵심 메시지**: 학습 안 한 리듬에도 *우아하게* 대응한다.
- **서술할 내용**
  - OOD-low(학습보다 느림): zero-shot으로도 in-dist 수준 tracking 유지.
  - OOD-high(빠름): 깨지지 않고 graceful degradation(성능이 급락이 아니라 완만히 저하).
  - 의미: 단순 암기가 아니라 phase 구조를 *일반화* 하고 있음.
- **시각자료**: `eval_figure4_zone_tracking_metrics.png`(zone별 |freq err| + PLV 막대, in-dist/OOD-low/OOD-high 구분).
- **발표 노트**: "느린 쪽은 거의 공짜, 빠른 쪽은 완만한 한계"라는 비대칭을 정직하게.

## Slide 29 — Result 4: Sync Loss Ablation  ★[branch: feature/final-sync-ablation-results]
- **핵심 메시지**: sync loss가 *정말로* 기여하는지, λ는 왜 0.12인지 분리 검증.
- **서술할 내용 (브랜치 내용 — 아래는 추정 골격, 확인 후 확정 예정)**
  - sync 적용 전/후(Trajectory vs Trajectory+Sync) 직접 대비: in-dist 품질과 frequency tracking이 *동시에* 개선되는지.
  - **λ(phase loss 가중치) sweep**: 예) λ ∈ {0, 0.06, 0.12, 0.24, …}에서 |freq err|·PLV·reward의 trade-off → λ=0.12 선택 근거.
  - (가능 항목) phase warmup 유무, fine-tune epoch 수에 따른 민감도.
- **시각자료**: λ sweep 곡선(λ vs PLV / |freq err| / reward) 또는 sync 전/후 막대 비교. → **브랜치의 실제 figure/표로 교체 필요**.
- **발표 노트**: "최종 ours의 하이퍼파라미터는 임의가 아니라 ablation으로 정했다" — 엄밀성 어필.
- ⚠️ **확인 요청 항목**: 이 브랜치가 (a) λ sweep인지, (b) sync on/off 최종 표인지, (c) 또 다른 ablation인지에 따라 슬라이드를 1장→2장으로 늘릴 수도 있음.

## Slide 30 — Result 5: Continuity / Smoothness Analysis  ★[branch: continuity]
- **핵심 메시지**: 생성된 보행이 *끊김 없이 매끄러운가* 를 본다.
- **서술할 내용 (브랜치 내용 — 아래는 추정 골격, 확인 후 확정 예정)**
  - diffusion policy의 알려진 이슈: receding-horizon으로 action chunk를 이어 실행할 때 **chunk 경계에서 불연속(jerk)** 발생 가능.
  - 가설: phase(trajectory) 정보가 chunk 간 위상을 이어주어 **경계 연속성/부드러움**을 개선한다.
  - 측정(추정): chunk 경계 action 점프, jerk/acceleration 변동, 또는 phase 연속성 지표를 4개 모델에서 비교.
- **시각자료**: chunk 경계 부근 action/phase 시계열 확대(연속 vs 불연속 대비) 또는 smoothness 막대 비교. → **브랜치의 실제 정의/figure로 교체 필요**.
- **발표 노트**: "품질 = 빠른 게 아니라 *매끄럽고 안정적인* 보행"이라는 현실 관점과 연결(파트 H의 현실 응용으로 이어짐).
- ⚠️ **확인 요청 항목**: "continuity"가 (a) chunk 경계 action 연속성인지, (b) phase 연속성(PLV와 다른 지표)인지, (c) 장기 rollout 안정성인지 확정 필요. 정의에 따라 측정 지표·그림이 달라짐.

## Slide 31 — 정성적 결과 (Qualitative)
- **핵심 메시지**: 숫자 뒤의 "실제로 어떻게 걷는가".
- **서술할 내용**
  - 대표 rollout 영상: vanilla(어색/불안정) vs ours(리듬감 있는 안정 보행) 비교.
  - phase tracking 시계열: 명령 phase vs 측정 phase가 ours에서 거의 겹침.
- **시각자료**: `eval_figure5_phase_tracking_timeseries.png`(모델별 panel) + (가능하면) 영상 GIF 2컷 나란히.
- **발표 노트**: 영상이 있으면 여기가 발표의 감정적 클라이맥스. 10–15초 재생.

## Slide 32 — 결과 종합: 4개 Contribution 검증
- **핵심 메시지**: 약속(Slide 8)을 전부 회수했다.
- **서술할 내용**
  - 체크리스트: ① 품질↑(Table1) ② 제어성(Table2) ③ OOD 일반화(fig4) ④ sync 동기화(ablation). 각 항목에 핵심 수치 1개씩.
  - 한 줄 결론: *"phase trajectory + frozen-estimator sync = 명령 가능한, 매끄러운 controllable locomotion."*
- **시각자료**: Slide 8과 동일한 4카드 레이아웃에 ✅ + 대표 수치 채워넣기(약속↔회수 대칭).
- **발표 노트**: 청중이 "전부 증명됐다"는 closure를 느끼게.

---

# 파트 H — Discussion & Conclusion

## Slide 33 — Limitations (정직한 한계)
- **핵심 메시지**: 무엇이 아직 부족한지 먼저 인정한다.
- **서술할 내용**
  - 학습 데이터가 좁은 단일 주파수 분포(≈2.0 Hz) → 진짜 다주파수 일반화는 미검증.
  - 일부 결과의 seed 분산(특히 archive한 추론 시점 sampling); OOD-high에서의 한계.
  - Ant는 정통 quadruped benchmark이나 실로봇이 아님(sim-only).
- **시각자료**: 한계 3개 카드(데이터 / 분산 / sim2real). 과장 없는 톤.
- **발표 노트**: "한계를 아는 것"이 연구 성숙도. 교수님이 신뢰하는 포인트.

## Slide 34 — 현실 응용 함의 (AI + X 회귀)
- **핵심 메시지**: 이 결과가 현실에서 왜 의미 있는가로 되돌아온다.
- **서술할 내용**
  - "보행 리듬을 명령으로 modulate" = 지형 적응(느린 신중 스텝/빠른 스텝), 에너지 효율, 외부 명령 추종의 직접적 토대.
  - 생성 모델의 multimodality + phase 제어 = *데이터로부터* 적응형·제어형 보행을 얻는 일반 레시피(다른 morphology로 확장 가능).
  - Slide 7의 novelty↔현실 비유를 닫으며 수미상관.
- **시각자료**: 현실 시나리오 아이콘(계단/빙판/평지) + "command → rhythm → adapt" 화살표.
- **발표 노트**: 교수님 평가축(AI+X)을 마지막에 한 번 더 또렷이.

## Slide 35 — Future Work
- **핵심 메시지**: 다음 단계는 명확하다.
- **서술할 내용**
  - 다주파수/다gait 데모 확보 → 진짜 multi-frequency controllability.
  - archive했던 추론 시점 Phase-Consistent Sampling을 분산 안정화 후 sync loss와 결합.
  - sim-to-real(실 quadruped) 이식, 외부 velocity/terrain 명령과의 결합.
- **시각자료**: 로드맵 화살표 3단계(data → method → real robot).
- **발표 노트**: "오늘이 끝이 아니라 발판"이라는 톤.

## Slide 36 — Conclusion (+ References / Q&A)
- **핵심 메시지**: 한 장으로 전체를 요약.
- **서술할 내용**
  - 문제(보행의 multimodality) → 도구(diffusion policy) → 빈틈(phase 미사용) → 해법(phase **trajectory** conditioning + frozen sync) → 증거(4 contributions).
  - 핵심 수치 한 줄: in-dist PLV 0.912 / |freq err| 0.035, vanilla 대비 reward·velocity 대폭 향상.
  - 감사 + Q&A. (References는 별도 슬라이드 또는 appendix: Chi et al. 2023, PAPL 2026 등)
- **시각자료**: spine 한 줄 다이어그램(문제→도구→빈틈→해법→증거) 1컷.
- **발표 노트**: 마지막 문장은 Slide 7/34의 "명령 가능한 보행 리듬"으로 닫기.

---

## 부록(Appendix) 후보 — 본문 30+장 외 예비
- A1. ε-prediction / DDPM·DDIM 상세 수식, scheduler 설정.
- A2. 학습 곡선 모음(`vanilla_dp_loss`, `phase_periodic_loss`, `phase_trajectory_loss`).
- A3. 데이터 필터 임계값 표 & frequency window 통계.
- A4. 전체 하이퍼파라미터 표(batch/lr/epoch/EMA/seed).
- A5. 팀원 역할 분담 & 일정.

---

## ⚠️ 확정 전 확인이 필요한 2개 지점 (브랜치 미접근)

제 도구가 `feature/final-sync-ablation-results`, `continuity` 두 브랜치의 파일을 직접 열 수 없었습니다(GitHub raw/branch URL 접근 제한). 그래서 **Slide 29 / Slide 30**은 맥락 기반 *추정 골격*입니다. 아래만 알려주시면 두 슬라이드를 실제 내용으로 정밀하게 확정(필요 시 각 1→2장 확장)하겠습니다.

1. **Slide 29 (sync ablation)**: 이 브랜치는 λ sweep인가요, sync on/off 최종 비교표인가요, 아니면 또 다른 ablation인가요? (대표 figure/표 파일명 또는 핵심 수치)
2. **Slide 30 (continuity)**: "continuity"가 ① chunk 경계 action 연속성, ② phase 연속성(PLV와 별개 지표), ③ 장기 rollout 안정성 중 무엇인가요? 측정 지표/그림 정의를 알려주세요.

(가장 빠른 방법: 두 브랜치의 README 또는 해당 결과 셀/표를 여기에 붙여넣어 주시면 즉시 반영하겠습니다.)
