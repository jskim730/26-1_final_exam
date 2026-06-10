# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import os
from pathlib import Path
from gr.asset.shadow_hand import SHADOW_HAND_CFG
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.envs import DirectRLEnvCfg, ViewerCfg
from isaaclab.markers import VisualizationMarkersCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import PhysxCfg, SimulationCfg
from isaaclab.sim.spawners.materials.physics_materials_cfg import RigidBodyMaterialCfg
from isaaclab.utils import configclass
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[6]

# Sequence selection via GR_SEQ env var ("1"/"2"/"3"), default "1" (main). Keeps a SINGLE config file
# whose ONLY per-sequence difference is the data path + END_FRAME, so two sequences can train in PARALLEL
# (separate processes: GR_SEQ=1 and GR_SEQ=3) and a resumed run re-selects the right data deterministically.
# The old hardcoded comment-block toggle was NOT resume-safe when sharing the file across parallel runs (a
# resumed run would read whichever block was last uncommented). All reward/network hyperparameters stay
# identical across sequences -> grading-identical-config holds (only the data differs). To resume a non-main
# run you MUST pass the same GR_SEQ (e.g. `GR_SEQ=3 ... bash run_resume.sh`).
_GR_SEQ = os.environ.get("GR_SEQ", "1")
_SEQ_TABLE = {
    "1": ("sequence1", "sequence1.usd", 250),   # main
    "2": ("sequence2", "sequence2.usd", 660),   # optional 1
    "3": ("sequence3", "sequence3.usd", 510),   # optional 2
}
if _GR_SEQ not in _SEQ_TABLE:
    raise ValueError(f"GR_SEQ must be one of {sorted(_SEQ_TABLE)}, got {_GR_SEQ!r}")
_seq_dir, _obj_usd, END_FRAME = _SEQ_TABLE[_GR_SEQ]
SEQ_PATH = str(PROJECT_ROOT / "data" / "HOCAP" / _seq_dir / f"{_seq_dir}.pt")
OBJ_PATH = str(PROJECT_ROOT / "data" / "HOCAP" / "object" / _obj_usd)


@configclass
class GrEnvCfg(DirectRLEnvCfg):
    play = False
    asymmetric_obs = False
    
    # obs = current state (117) + task dims (73) + dynamics/rotation augmentation (18) = 208
    #   current: hand_kpts(63) + hand_dof(18) + obj_pos(3) + obj_rot_6d(6) + last_action(27)
    #   task:    phase(1) + hand_kpt_err(63) + obj_pos_err(3) + obj_rot_ref_6d(6)
    #   augment: obj_rot_err_6d(6) + obj_linvel(3) + obj_angvel(3) + obj_linvel_ref(3) + obj_angvel_ref(3)
    #     rot-error and object/ref velocity were the missing signals for tracking the big flips
    #     (rot END err 86-180 deg) and for detecting slip/drop at the placement/release phase.
    observation_space = 208

    # env
    decimation = 4
    obs_type = "full"

    table_upper_z = 0.4
    table_pos_z = -0.1

    hand_mount = 'robot0_hand_mount'
    root_body = 'robot0_palm'


    body_to_kpts_except_fingertips = [0, 5, 20, 22 , 1, 11, 16, 2, 12, 17, 3, 13, 18, 9, 19, 21]
    MANO_kpts = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    MANO_kpts_except_fingertips = [0, 1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19]
    MANO_fingertips = [4, 8, 12, 16, 20]
    MANO_rigids = [0, 5, 9, 13]

    seq_ref_path = SEQ_PATH
    obj_path = OBJ_PATH
    start_frame = 0
    end_frame = END_FRAME
    
    action_fps = 30
    episode_length = max(1, end_frame - start_frame)
    num_frame_chunk = episode_length
    episode_length_s = (((num_frame_chunk)*10)//action_fps)/10.0
    warm_up_epochs = 0


    # PD controller gains
    K_pos = 4000
    K_rot = 160

    # simulation
    sim: SimulationCfg = SimulationCfg(
        dt=1 / (action_fps * decimation),
        render_interval=decimation,
        physics_material=RigidBodyMaterialCfg(
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
        physx=PhysxCfg(
            bounce_threshold_velocity=0.2,
            gpu_max_rigid_patch_count=5 * 2**17,
            gpu_total_aggregate_pairs_capacity=2 ** 22,
        ),
    )

    # robot
    robot_cfg: ArticulationCfg = SHADOW_HAND_CFG.replace(
        prim_path="/World/envs/env_.*/Robot"
    )
    
    # camera
    viewer: ViewerCfg = ViewerCfg(
        eye=(3.0, 3.0, 2.0),
        lookat=(1.0, 1.0, 0.2),
    )

    num_revolving_joints = 22
    actuated_joint_names = [
        "robot0_FFJ3",
        "robot0_FFJ2",
        "robot0_FFJ1",
        "robot0_MFJ3",
        "robot0_MFJ2",
        "robot0_MFJ1",
        "robot0_RFJ3",
        "robot0_RFJ2",
        "robot0_RFJ1",
        "robot0_LFJ4",
        "robot0_LFJ3",
        "robot0_LFJ2",
        "robot0_LFJ1",
        "robot0_THJ4",
        "robot0_THJ3",
        "robot0_THJ2",
        "robot0_THJ1",
        "robot0_THJ0",
    ]
    fingertip_body_names = [
        "robot0_thdistal",
        "robot0_ffdistal",
        "robot0_mfdistal",
        "robot0_rfdistal",
        "robot0_lfdistal",
    ]

    end_joint_names = [
        "robot0_FFJ3",
        "robot0_MFJ3",
        "robot0_RFJ3",
        "robot0_LFJ3",
        "robot0_THJ3",
    ]
    
    num_dof = len(actuated_joint_names)
    action_space = 9 + num_dof # trans + rotation + joint
    state_space = 0
    
    object_cfg: RigidObjectCfg = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Object",
        spawn=sim_utils.UsdFileCfg(
            usd_path=obj_path,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=False,
                disable_gravity=False,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=0,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.1),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.8, 0.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.0, 0.0, 1.0),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # Scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=2048, env_spacing=2.5, replicate_physics=True, clone_in_fabric=False
    )
    
    goal_marker_cfg: VisualizationMarkersCfg = VisualizationMarkersCfg(
        prim_path="/Visuals/goal_markers",
        markers={
            "goal": sim_utils.UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Shapes/sphere.usd",
                scale=(0.03, 0.03, 0.03),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.0, 0.0),
                ),
            )
        }
    )

    debug_marker_cfg: VisualizationMarkersCfg = VisualizationMarkersCfg(
        prim_path="/Visuals/debug_markers",
        markers={
            "debug": sim_utils.UsdFileCfg(
                usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/Shapes/sphere.usd",
                scale=(0.03, 0.03, 0.03),
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.0, 1.0, 0.0),
                ),
            )
        }
    )

    table_cfg: RigidObjectCfg = RigidObjectCfg(
        prim_path="/World/envs/env_.*/table",
        spawn=sim_utils.CuboidCfg(
            size=(1.5, 1.5, 2*(table_upper_z-table_pos_z)),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=True,
                disable_gravity=True,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.5, 0.5, 0.5)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.0, 0.0, table_pos_z)),
    )

    action_dt = 1 / action_fps
    
    # reward weights: each r_* term is in [0,1] after coefficient rescaling. Rotation (r_or) is
    # the placement bottleneck: at the current operating point r_op≈0.70 but r_or≈0.22, so position
    # out-rewards orientation ~3x and the object topples instead of standing upright. Bump w_or to
    # emphasize the failing orientation dimension; kept moderate (1.5, not higher) to avoid the
    # "one term dominates" failure the instructor warned about — dial back if r_or saturates near 1.
    w_hand = 1.0
    w_ft = 1.0
    w_op = 2.5        # Path B v4 (2026-05-27): 1.0->2.5. v3 grips but HOLDS the object still on the table;
                      #   r_op is the only lift driver and at w=1.0 the ~0.87 reward gain from lifting didn't
                      #   beat the drop-risk (losing the ~1.7 grip rewards). 2.5 makes following the lift
                      #   trajectory clearly worth it WITHOUT touching the (unchanged) grip rewards, so grasp
                      #   is preserved. Moderate enough to avoid the instructor's "one term dominates" trap.
    op_z_lin_scale = 0.30  # Z-LINEAR LIFT FIX (2026-06-04): r_op's vertical part is clamp(1 - |dz|/scale, 0, 1)
                      #   (angle-linear, like or_linear) while the xy part stays exp(-10*err_xy). The old
                      #   exp(-10*||3D err||) had a FLAT TAIL in the deep-lift region (seq3 lift 27cm ->
                      #   exp(-2.7)=0.067, grad ~1.7/m -> no up-pull), so seq3 never learned the lift
                      #   (etlift_v1: horizon opened to 437, grip firm, actual_lift ~0). The linear z gives
                      #   a CONSTANT grad ~w_op/(2*scale)=4/m out to the peak. scale=0.30 >= every seq's peak
                      #   lift (13/14/27cm) so the term never bottoms out. seq-agnostic (z err in meters).
                      #   Pairs with et_lift_lag_frac reverted to 0.0 (ET relaxation was the wrong lever: it
                      #   removed the lift-or-die pressure and created a comfortable grounded basin).
    carry_pos_lift_gate = True  # SEQ2 SLIDE FIX (2026-06-04): during the CARRY phase, gate r_op_xy + r_or by
                      #   actual lift (carry_gate = (1-c) + c*lift_track). seq2's ref lifts then PLACES the object
                      #   BACK on the table, so averaged r_op_xy/r_or were fully gameable by SLIDING the grounded
                      #   object to the right xy+yaw with NO grasp/lift (enclosure~0, actual_lift~0; play-confirmed
                      #   slide optimum). z-linear r_op_z docks height but r_op=0.5*(xy+z) + full r_or still paid the
                      #   slide. Gate removes the slide-collectable xy/rot credit ONLY while ref is airborne and the
                      #   object is grounded; =1 outside carry (seq1 place-down untouched) and =1 when lifted to ref
                      #   (seq1/seq3 carry untouched -> no regression). ONE seq-agnostic rule; mirrors the existing
                      #   carry-gates on r_grasp/r_hold/r_grip_pose. Toggle for ablation.
    carry_pos_grip_gate = True   # SEQ3 BALANCE-LIFT FIX (2026-06-07, [[seq3-balance-lift-no-grip]]): the
                      #   lift-only carry gate above stopped seq2's no-lift SLIDE but not seq3's lift-WITHOUT-grip
                      #   BALANCE -- the book RESTS on the hand (contact_closure~0) yet lift_track>0, so the gate
                      #   passed and paid full xy/rot credit (play-confirmed; TB contact_closure_ema flat ~0 over
                      #   2800 ep with actual_lift up to 20cm -> hand-tracking + rotation both fail). Multiply the
                      #   carry gate by a SATURATING grip_factor = clamp(grip_contact_base/grip_gate_ref, 0, 1):
                      #   1.0 once a firm grip exists (NO-OP for seq1, enclosure 0.77 >> ref) and ~0 for the
                      #   balance (cc~0), removing its free xy/rot credit so a real grip becomes necessary.
                      #   Threshold not raw-multiply -> a soft scoop grip is not penalized. False -> grip_factor=1
                      #   = exact revert to the lift-only gate. seq-agnostic.
    grip_gate_ref = 0.12         # saturation threshold for carry_pos_grip_gate's grip_factor. Sits in the empty
                      #   gap between no-grip (grip_contact_base~0, seq3 balance) and a real grip (seq1 enclosure
                      #   0.68-0.77); 0.1-0.2 all safe. data-derived, IDENTICAL across sequences (grading rule).
    use_comove_hold = False  # REVERTED (2026-06-05): comove rewarded "object co-moves with fingertips" which
                      #   BATTING also satisfies -> it was the mechanism that opened seq2's horizon by gaming
                      #   (play-confirmed: weird/batted grasp, not a correct lift). seq3's mass-anneal lift was
                      #   verified WITHOUT comove anyway. The lift-onset grip-sharpening lever is the cleaner,
                      #   non-gameable grasp signal (track the ref's tight grip precisely). Toggle kept for ablation.
                      #   ---- original rationale (now superseded) ----
                      #   SEQ2/3 GRASP FIX (2026-06-04): r_hold's contact gate = max(enclosure, comove)
                      #   instead of just enclosure. enclosure is an OPPOSITION-pinch metric (thumb x opposing
                      #   finger TIP force); verify_seq2_enclosure.py proved seq2/seq3 grasps are SAME-SIDE
                      #   (0% opposition vs seq1's 100%) so enclosure ~ 0 there -> r_hold was structurally dead
                      #   -> no transferable grasp learned. comove = (object near a fingertip) x (object linvel
                      #   matches mean fingertip linvel): a free object held aloft & co-moving with the hand is
                      #   grasped regardless of topology, no opposition/tip-force needed. max() -> seq1's pinch
                      #   keeps selecting enclosure (r_hold ~unchanged, minimal seq1 impact); seq2/3 use comove.
                      #   lift_track still zeroes r_hold on the ground (no pre-lift exploit). seq-agnostic.
    comove_vel_k = 3.0      # velocity_lock = exp(-comove_vel_k * ||v_obj - mean v_fingertip||). Lenient (3.0)
                      #   so the rotate phase's lever-arm relative velocity isn't over-penalized; a dropped
                      #   object (rel vel ~1 m/s) still collapses to exp(-3)=0.05.
    comove_prox_slack = 0.10  # m: proximity = exp(-5*relu(d_min - slack)). 10cm slack so a grip on the far end
                      #   of an elongated object (seq2 closest tip ~6-8cm from obj origin) scores ~1; only an
                      #   object knocked >10cm from every fingertip is suppressed.
    w_or = 2.5        # Path B v5 (2026-05-27): 1.5->2.5 to drive rotation as hard as lift (w_op), now that
                      #   r_or has a usable gradient (see rot_k). v4 grips+lifts but does NOT tilt at all.
    rot_k = 1.0       # Path B v5: r_or = exp(-rot_k * geodesic_angle_rad). Replaces exp(-40*err^2) which was
                      #   FLAT ZERO above ~90deg (no gradient to start the 135deg/180deg tilt). rot_k~1.0 keeps
                      #   a monotone gradient across the full 0..180deg range (180->0.04 ... 45->0.46).
                      #   USED ONLY when or_linear=False.
    or_linear = True  # 2026-06-01: r_or = clamp(1 - theta/pi, 0, 1) instead of exp(-rot_k*theta). WHY:
                      #   dump analysis proved the policy does a WRONG-AXIS vertical YAW, not the reference
                      #   pour (seq1: act-axis vs ref-axis 50-70deg apart, geodesic stuck at ~126-130deg;
                      #   v6-SOLVED shows 7deg axis gap / 19deg geodesic). The wrong-axis yaw is a local
                      #   optimum that exp(-k*theta) CANNOT escape: its gradient is ~flat at theta~126deg
                      #   (exp(-2.2)=0.10), so there is no pull along the geodesic from the yaw basin toward
                      #   the pour. The angle-LINEAR shape has CONSTANT gradient (w_or/pi) across the whole
                      #   0..pi range -> ~3.4x stronger at 135deg, ~7x at 180deg -> the lever to drag the
                      #   orientation out of the yaw basin onto the correct pour axis. r_or is a gate-free
                      #   base term -> avoids palmframe's enclosure catch-22. Same [0,1] range as exp so
                      #   w_or=2.5 ceiling is unchanged. seq-agnostic. Trade-off: weaker near theta~0
                      #   (1/pi=0.32 vs exp 1.0) -> slightly less fine-tracking precision; revisit if the
                      #   landing rotation regresses. See memory rotation-wrong-axis-yaw. False -> exp.
    or_axis_align = True   # [EXPERIMENT 2026-06-08 axisalign_v1; byte-identical rollback = set back to False]
                      #   ROTATION-AXIS PURITY (seq2/seq3 wrong-axis fix). or_linear fixed the
                      #   rotation MAGNITUDE (seq2 reaches 150deg vs ref 149) but r_or is total-geodesic =
                      #   AXIS-AGNOSTIC: the policy can spend that magnitude on the cheap vertical-YAW axis and
                      #   still collect r_or. Frame-0 play dump (ep7100): seq2 carry off-axis SWING 52deg /
                      #   seq3 57deg / seq1 only 3.9deg (clean pour). When True, add a swing-twist term that
                      #   decomposes the actual rotation-from-frame0 into TWIST about the reference axis +
                      #   SWING (off-axis) and penalizes the swing angle, angle-linear like or_linear,
                      #   magnitude-gated by ref_rot_angle. OBJECT-ONLY -> grip-safe (never pulls the hand off
                      #   the object, unlike the palmframe / absolute-MANO graveyard); seq-agnostic.
                      #   2026-06-08 ACTUAL-ROTATION COUPLING: term *= actual_frac=clamp(actual_rot/ref_rot), so a
                      #   STILL object earns 0. The original 1-swing/pi form paid a still object FULL -> a free
                      #   ~0.39 "park" reward that broke seq1 after releasehand (which had no axis term). Now
                      #   seq1-neutral BY CONSTRUCTION (still->0) AND a stronger on-axis driver for seq2/seq3.
                      #   See env.py r_or_axis block + [[release-hand-return-term]].
                      #   Default False = byte-identical rollback. The byte-identical SUBMISSION must use the
                      #   SAME value on all 3 sequences (it is data-independent). See seq2-finger-manipulation.
    w_or_axis = 1.0   # weight for the or_axis_align swing term (active only when or_axis_align=True). ~0.4*w_or
                      #   so it shapes the axis without out-rewarding the r_or/r_op magnitude terms.
    or_axis_gate_r_or = True      # SEQ2/3 WRONG-AXIS FIX (2026-06-10): r_or by itself is geodesic-only, so a
                                  #   policy can spend the rotation magnitude on a cheap off-axis/yaw motion and
                                  #   still collect most of the carry rotation credit. Keep the additive
                                  #   r_or_axis shaping above, but also multiply the CARRY portion of r_or by an
                                  #   axis-purity factor derived from the same swing angle. This turns axis purity
                                  #   from "extra bonus" into "you cannot get full r_or on the wrong axis".
    or_axis_gate_floor = 0.25     # floor for the r_or axis gate. Wrong-axis rotations still keep 25% of r_or so
                                  #   early learning is not starved; clean-axis rotations keep 100%.
    # Path B v4: "gripping" threshold for the pull-up-when-gripping hand-target blend (fraction of the 5
    # fingertips in contact at which the in-window r_hand target fully switches to the lifted MANO pose).
    lift_contact_frac = 0.4   # 0.4 => >=2 of 5 fingertips in contact counts as a grip -> pull up to lift

    # Tolerance bands DISABLED (2026-05-25): the band gave full reward within 2-3cm, which removed
    # exactly the fingertip-precision gradient that closes the grip. The grasp is LATENT in the
    # human demo — tracking the MANO fingertips precisely puts the fingers where the human's were
    # (wrapped on the object), so a sub-cm fingertip reward is what recovers the demonstrated grasp
    # from frame 0. 0.0 = no band (pure exp tracking). Object terms now compete via w_grasp + r_op,
    # not by hobbling the hand. Raw errors are still logged to TB.
    hand_tol = 0.0    # m: no band (was 0.03)
    ft_tol = 0.0      # m: no band (was 0.02) — fingertip precision drives the grasp

    # r_orient: hand-orientation tracking, GATED to grip+release (2026-06-02). Wrist ROLL is a
    # near-null-space direction of the position rewards (a full palm flip moves the 21 keypoints only ~3cm
    # when the hand is flat), so r_hand/r_ft cannot stop the retreat palm-flip orlin's lift+pour excites
    # NOR finely drive the pour orientation. r_orient tracks the MANO-reference palm FRAME directly,
    # angle-LINEAR (clamp(1-theta/pi)) like or_linear. GATE in gr_env = max(enclosure, release_seq):
    # ON when actually gripping (enclosure -> helps lift/hold/pour rotation) OR in the post-grip release
    # retreat (-> fixes the flip); OFF during the empty-handed approach so it never distracts grasp
    # DISCOVERY. History: orient_v1(w=1.0, ALWAYS-ON) starved the grasp (orientation HAVEN, enclosure
    # 0.067@ep1655 vs orlin 0.37); orient_v2(w=0.3, always-on) STILL enclosure 0 @ep1149 = r_orient
    # anywhere in approach/grasp-learning corrupts it (user insight). Fix = the grip+release gate, which
    # frees w back to 1.0 (the enclosure ramp prevents the haven; absolute MANO target has no position
    # offset so it rotates in place without the palmframe catch-22). Seq-agnostic.
    w_orient = 1.0
    orient_use_grip_quality_gate = False  # Stage carefully (2026-06-10): the grip_quality carry gate can help
                                          #   seq2/3 topology, but it changes seq1's already-validated carry
                                          #   wrist-orientation schedule. Keep the old enclosure+release gate by
                                          #   default; turn this on only after the r_or axis gate is validated.

    # r_release_hand: release-phase hand-RETURN term (B, 2026-06-07). DIAGNOSIS (frame-0 play dump +
    # action/dof_vel dump): after the object is PLACED (release_seq), the policy parks the hand near the
    # object's former location instead of retreating to the MANO home pose -- seq1 ends hand_err ~25cm
    # (wrist 27cm from the reference home). reg and base-rate-limit were BOTH ruled out as the cause:
    #   - reg: extra move-cost only 0.026/frame vs r_hand RETURN gain 0.473/frame (reg is NOT contesting it)
    #   - rate: robot reaches 1.7cm/frame (95pct 1.4); the ref retreat mean is 0.75cm/frame -> reachable
    # Root cause = SALIENCE: the retreat is the last ~30-60 frames, ~0.6% of the return, so PPO never
    # climbs the (present but weak) always-on r_hand gradient there. Fix = make the retreat salient with a
    # release-GATED, distance-LINEAR hand-return reward (constant gradient all the way home, mirroring the
    # or_linear / z-linear r_op breakthroughs; exp(-k*err^2) flattens far out where the gap is largest).
    # GATE = self.release_seq[t], a HARD 0/1 reference-time schedule that is identically 0 across ALL of
    # approach+carry, so this term is EXACTLY 0 outside the post-place retreat (no reward/gradient leak into
    # grasp/lift). SEQ IMPACT (verified from obj_trans refs under THIS cfg): seq1 release=63f, seq2=167f
    # (both place the object down and the MANO hand returns home -> seq1 fixed + seq2 same-pattern benefit),
    # seq3 release=0f (held aloft to T-1) -> release_seq identically zero -> term NEVER fires -> seq3
    # byte-identical. Independent of policy behavior (reference-time gated). ROLLBACK: release_hand_track=False.
    release_hand_track = True
    w_release_hand = 1.0             # restored 2.0->1.0 (2026-06-10): instead of brute-forcing the return weight,
                                     #   r_release_open below attacks the ROOT cause (grip coupling pins the hand).
                                     #   r_release_hand is now OPEN-GATED in gr_env (x (1-grip_release)): it pays
                                     #   only when the hand is open, killing the "return while gripping" drag.
    # r_release_open: release-phase grip-OPEN penalty (2026-06-10). The hand parks near the placed object because
    # it never lets go -- grip_quality stays high through the release window, mechanically coupling hand to object
    # so r_release_hand cannot pull it home. This term subtracts the live grip during release, pushing the policy
    # to OPEN the hand once the object is down. Gated by the SAME hard 0/1 release_seq schedule as r_release_hand
    # (0 across approach+carry -> no leak into grasp/lift; seq3 release empty -> identically 0 -> byte-identical).
    # grip_quality clamped to [0,1] (enclosure can exceed 1) so the penalty never dominates (instructor warning);
    # logged separately. ROLLBACK: release_open_penalty=0.0. PAIRS WITH w_release_hand (return) above.
    release_open_penalty = 1.0
    release_hand_lin_scale = 0.30    # m: r = clamp(1 - hand_err/scale, 0, 1); 0.30 follows the op_z_lin_scale
                                     #   convention (>= the ~25cm failure gap so it never bottoms out) -> a
                                     #   constant ~3.3/m pull toward the home pose across the whole retreat.
    release_place_tol = 0.15         # m: r_release_hand *= clamp(1 - obj_err/tol). The hand-RETURN reward is
                                     #   gated by the object STAYING at its reference -> dragging the placed
                                     #   object off-ref kills the return reward (force-grip gate was a no-op:
                                     #   the drag is a low-force cling). 0.15 keeps a live gradient at the
                                     #   observed 13cm-drag failure point while ~0 reward there. ROLLBACK: large.

    action_penalty_scale = -0.008   # Path B v6 (2026-05-27): -0.004->-0.008. The v5 dump showed the hand
                                    #   trembles ~1.9x the human reference; weak smoothness reg let the
                                    #   policy make jittery per-step corrections while gripping the free
                                    #   object. Penalize action magnitude more (2x).
    dof_penalty_scale = -0.005      # Path B v6: -0.001->-0.005 (5x). dof_vel^2 is the direct anti-jitter
                                    #   term (penalizes fast joint motion = the tremble). Moderate bump to
                                    #   smooth the hand WITHOUT making it sluggish enough to hurt the
                                    #   1cm/6deg tracking; validate both (tracking + jitter ratio) by dump.
    # Path B v6 regularization ANNEAL: the above (full) smoothness reg suppresses the exploratory finger
    # motion needed to DISCOVER the grasp from scratch (a fresh run never grips). So multiply action/dof
    # penalties by reg_mult, which starts low (exploration) and ratchets to 1.0 once the grasp is established.
    reg_anneal_start_mult = 0.25    # initial fraction of full reg (0.25*-0.005=-0.00125 dof ~ the v3/v5 low reg)
    reg_anneal_grasp_thresh = 0.20  # start ramping reg up once EMA(r_grasp) exceeds this (grasp established)
    reg_anneal_step = 0.004         # reg_mult increment per reset batch (~190 batches low->full = gradual)
    reg_anneal_ema = 0.97           # EMA factor for the r_grasp signal that gates the ramp

    act_moving_average = 0.5
    global_moving_average = 0.2

    vel_obs_scale = 0.2

    # --- Early Termination (ET) ---
    # Cut the episode when the hand/object drift too far from the reference. This removes the
    # constant "free" object reward a do-nothing policy used to collect for the full episode.
    use_et = True
    et_obj_pos_thresh = 0.15      # m: object diverged from reference -> terminate (seq2/3: 0.12→0.15)
    et_obj_pos_thresh_grip = 0.15 # m: Path B v7 (2026-05-28) re-tightened from 0.30 back to 0.15. The
                                  #   0.30 relax let envs survive 30cm drift during 150/250 frames -> reached_end_rate
                                  #   ~0.9 -> forward-horizon curriculum opened in ~80 ep (v8/v9) vs v6's ep1517.
                                  #   Without horizon scaffolding the policy never learned approach-then-grasp
                                  #   stage-by-stage and parked at "touch but don't squeeze" (TB ep2400: r_grasp=0,
                                  #   enclosure=0.0001). Re-tightening forces ET-based survival = horizon grows
                                  #   only as policy actually masters each segment, matching v6's SOLVED dynamics.
    et_hand_thresh = 0.30         # m: mean hand-keypoint divergence -> terminate
    et_grace_steps = 15           # steps after reset during which ET is disabled
    et_lift_lag_frac = 0.0        # REVERTED 2026-06-04: 0.5 -> 0.0 (flat wall). The lag-forgiveness experiment
                                  #   (main_seq3_etlift_v1) FALSIFIED the runway hypothesis: horizon opened to
                                  #   437 and the grip was firm (enclosure 0.90) but actual_lift stayed ~0 and
                                  #   r_hold ~0 -> forgiving the lag just removed the lift-or-die pressure and
                                  #   gave the policy a comfortable grounded basin (grip on table, track xy).
                                  #   Per the falsifiable note, that == a CAPABILITY problem, not runway -> the
                                  #   fix is denser lift shaping (op_z_lin_scale: z-linear r_op), not ET relax.
                                  #   Back to the flat wall so staying grounded past the lift frames still dies,
                                  #   and the new constant z-gradient now actually points the way up.

    # --- Forward-horizon curriculum (the single training backbone for all 3 sequences) ---
    # The data has no per-frame finger pose (`hand_dof_seq` is all zeros), so a mid-trajectory
    # reset drops a lifted object. Instead always start at frame 0 (the only valid reset, and the
    # play/eval condition) and grow the episode horizon as the policy masters the current frontier,
    # forcing the contiguous approach->grasp->lift->place skill that a frame-0 play rollout requires.
    # seq1 lift spans frames ~39-186 (object reaches +13cm at frame 156), so the horizon must reach
    # into them. SINGLE CONFIG: identical for all 3 sequences (grading: same hyperparameters); only
    # the sequence data and VIDEO_LENGTH change. The horizon froze at frame 138 in an early run
    # because the grasp gave NO reachable gradient from an open hand (object won't move until
    # gripped); the friction-anneal bootstrap below now supplies that gradient (a clumsy grip can
    # already lift under high friction), so the horizon can advance through the grasp/lift.
    horizon_init = 30             # initial max steps from frame 0 (on-table approach is frames 0-38)
    horizon_step = 1.0            # base frames the horizon grows per qualifying reset batch (one-sided)
    horizon_advance_thresh = 0.5  # grow only when this fraction of finishing envs reached horizon w/o ET
    horizon_accel = 3.0           # adaptive: step scales up to horizon_step*(1+accel) when the frontier
                                  #   is cleared comfortably (advance>>thresh), so easy phases advance fast
                                  #   and hard phases (lift/place) self-throttle. Needed for seq2 (660)/seq3 (510).
    # CURRICULUM LIFT-GATE (2026-06-06): the horizon/anneal `advance` signal counted any episode that
    # reached the cap without ET, EVEN IF the object was never lifted. seq1 under the contact_v2 config
    # parked in a stable NO-LIFT equilibrium (object left on the table, hand nearby -> no ET -> horizon
    # opened to full, lift=0) [[contact-v2-breaks-seq1-lift]]. Gate `advance` on per-episode lift
    # adequacy = DEMAND-WEIGHTED MEAN of lift_track over the episode, where demand = un-dilated ref-lift
    # ramp (carry_lift_lo..hi; NOT carry_seq, whose backward dilation would demand lift during the
    # grounded pre-grip approach and stall the horizon at frame 0). An env counts as advanced only if
    # (no lift was demanded this episode) OR (mean lift_track on the demanded frames >= thresh). Seq-
    # agnostic (lift_track normalized by each seq's own ref height). Validated on dumps with the REAL
    # demand: lifting seqs score seq2=0.99 / seq3=0.74, the no-lift seq1=0.01 -> thresh 0.4 separates
    # cleanly with a 0.33 margin for seq3. MEAN (not worst-frame min) is essential: a good lifting policy
    # transiently hits lift_track~0 at the liftoff/touchdown edges, so strict-min falsely fails seq3.
    horizon_lift_gate = True
    horizon_lift_thresh = 0.4     # demand-weighted mean lift_track required to count an env as advanced
    lift_gate_bootstrap_all = False  # 2026-06-08: the blanket bypass (was True) disabled the lift-gate for
                      #   ALL topologies during the light-mass ramp, which REOPENED seq1's no-lift exploit (the
                      #   gate's whole job, [[contact-v2-breaks-seq1-lift]]) -> seq1 parked in no-grasp pose-mimicry
                      #   (grasp_ema/enclosure/contact all flat 0, actual_lift 0, lift_gate_pass_rate 1.0 @ lift 0).
                      #   Replaced by ref_scoop_opp_frac_thresh below: the bypass now keys on the REFERENCE grasp
                      #   topology (_ref_is_scoop, computed from demo geometry -> known BEFORE contact, so it still
                      #   solves seq2's chicken-egg) instead of the live _is_scoop or a blanket flag. seq1=pinch ->
                      #   gate enforced; seq2/seq3=scoop -> bypassed pre-contact. Kept as an explicit override
                      #   (True = force-bypass all, exact prior behavior). seq-agnostic.
    ref_scoop_opp_frac_thresh = 0.5  # _ref_is_scoop = (ref opposition-frame fraction < this). Over the carry
                      #   window, the fraction of frames where the thumb opposes ANY finger (side-cos<0) = a pinch
                      #   cage. VERIFIED (verify_seq2_enclosure.py): seq1=1.00 (pinch) vs seq2=0.00 / seq3=0.00
                      #   (same-side scoop) -> 0.5 is the max-margin split. Data decides the topology -> the SAME
                      #   byte-identical config classifies each sequence from its own demo geometry.

    # --- Phase-Aware grasp/hold reward (v1, 2026-05-29) ---
    # The old r_grasp = (ref_airborne * actual_lift) * pose_gate(MANO) * enclosure had two failure
    # modes: (1) chicken-and-egg — r_grasp = 0 until the object is already lifted, so the policy
    # got NO actionable gradient from an open hand on a grounded object; (2) pose_gate used absolute
    # MANO 21-kpt error, which CONFLICTED with r_reach (which intentionally pulls fingers AWAY from
    # MANO toward the grounded actual object). v10 with ET=0.15 made this worse by killing the
    # exploration episodes that could have learned a recovery grip after a miss (frame-0 rot 105 deg
    # in lift window). FIX: split into TWO complementary terms with object-frame pose gating.
    #
    # r_grasp (PRE-LIFT discovery): credits an opposition pinch on the still-grounded object inside
    # the grip window. Gate = grip_gate * (1 - actual_lift_factor) * pose_gate_obj * enclosure. As
    # the object rises (lift_factor -> 1) r_grasp dies and r_hold takes over -> no double-counting.
    # r_hold (POST-LIFT goal): credits actual holding. Gate = ref_airborne * actual_lift_factor *
    # enclosure. press pathology (enclosure > 0 with object on table) -> r_hold = 0 automatically.
    # pose_gate_obj = exp(-reach_k * d_obj) reuses r_reach's object-frame fingertip distance, so
    # pose check and r_reach pull are in the SAME coordinate frame (no internal tug-of-war).
    w_grasp = 0.5                 # PA v1: 1.0 -> 0.5. r_grasp is now the smaller "discovery" term;
                                  #   r_hold (1.5) is the larger "goal" term. peak grip-attempt total
                                  #   ~10.5 (incl. r_reach+r_close+r_op+r_or) vs holding total ~11.5 ->
                                  #   monotone phase ladder (approach 7 -> grip 10.5 -> hold 11.5).
    w_hold = 1.5                  # PA v1: NEW. > w_grasp so press path < lift path. < r_op+r_or sum
                                  #   (5.0) so tracking stays dominant -> "one term dominates" trap avoided.
    # LIFT DESATURATION (2026-05-30): r_hold's lift factor was actual_lift_factor = sigmoid(100*(lift-
    #   0.01)), which SATURATES at ~3-5cm -> r_hold maxed out before the object reached the ref height
    #   (seq1 13 / seq2 14 / seq3 27cm) so there was NO incentive to lift fully (ep4300 stalled at
    #   +4.7cm). Replaced (in gr_env r_hold) by the LINEAR completion ratio clamp(actual_lift/ref_lift,
    #   0,1): constant gradient across the whole lift (strong at break-off too), 0 when grounded, 1 at
    #   the ref height, normalized per-seq -> no hyperparameter needed.
    contact_force_thresh = 0.05   # N: legacy binary in-contact threshold (kept; r_grasp uses continuous)
    grasp_force_scale = 0.5       # N: per-fingertip normal force where tanh contact saturates. Small -> a
                                  #   light press already yields gradient; opposition product gates to a true cage.
                                  # NOTE (2026-05-31): briefly raised to 2.0 on a "grip too weak -> object slips
                                  #   during rotation" hypothesis, but the play video showed the object does NOT
                                  #   slip -- the HAND tilt oscillates (tilts, returns to neutral, tilts again),
                                  #   a rotation-TRACKING issue, not a grip-force one. Reverted to 0.5.
    grasp_contact_w = 0.25        # any-contact tail weight in enclosure (first-contact gradient).
                                  #   v6's value. Opposition product (max ~1.0) > any-contact (max 0.25)
                                  #   so a single-finger poke stays cheap; PA v1 keeps this value.
    # --- Contact-closure grip signal (2026-06-05, seq2 force-closure fix) [[seq2-contact-closure-grip]] ---
    # enclosure = thumb_tip x opposing-finger_tip force is an OPPOSITION-pinch metric -> structurally ~0 for
    # seq2/seq3's SAME-SIDE scoop grasps [[enclosure-structurally-zero-seq2-seq3]], so r_grasp/r_hold were dead
    # there. contact_closure is OPPOSITION-FREE: it requires the grip_contact_k STRONGEST fingertip contacts to
    # ALL press the object at once (product of the top-k saturated normal forces). A 4-finger scoop under a book
    # and a thumb-index pinch BOTH satisfy it. It is CONTACT-FORCE based (real PhysX normal force), so unlike the
    # kinematic comove fallback it CANNOT be gamed by BATTING: a ballistic object that has left the hand carries
    # zero fingertip contact force -> contact_closure -> 0. It enters the grip path ONLY as
    # grip_contact = max(enclosure, contact_closure), so:
    #   seq1 (pinch): opposition already drives enclosure high -> max() returns enclosure -> r_grasp/r_hold
    #                 within noise of the verified orlin config (top-2 of a pinch = thumb+finger = same pair).
    #   seq3 (scoop): enclosure~0 so contact_closure takes over, but it is gated by the SAME c*lift_track as
    #                 before -> it only pays ALONG seq3's existing mass-anneal lift+grip trajectory (reinforces,
    #                 introduces no new farmable optimum: cannot score without real lift AND real contact).
    #   seq2 (scoop): revives the dead grip signal -> r_grasp (pre-lift discovery) + r_hold (post-lift) fire.
    # Weights (w_grasp/w_hold) and the mass/friction gate (still enclosure_ema) are UNCHANGED, to bound the
    # seq1/seq3 perturbation. Toggle for ablation.
    use_contact_closure = True
    grip_contact_k = 2            # # of fingertips that must SIMULTANEOUSLY press (top-k product). 2 = a real
                                  #   two-point grip (anti single-finger-poke); a scoop presses 4 so 2 is lenient.
    lift_gate_margin = 0.02       # m: object considered airborne when ref z exceeds frame-0 rest z by this

    # --- Carry phase signal c[t] (verified lift-based, 2026-06-03) ---
    # carry_seq[t] = SMOOTH ramp of the reference lift height (above the frame-0 rest) between carry_lift_lo
    # and carry_lift_hi, backward-dilated by reach_pre_frames. It is the phase weight c[t] that gates every
    # carry-added grip term (r_grasp/r_hold/r_grip_pose/r_palm/r_close) and the absolute-fingertip
    # suppression -> "free objective = always-on base (r_hand_abs + r_op + r_or + r_orient); carry objective
    # = base + c * grip machinery". Replaces the previous BINARY grip window so the approach<->carry<->
    # release transitions carry continuous gradient. Verified seq-agnostic (verify_carry_lift.py): a single
    # contiguous carry block on ALL 3 sequences, bracketing >99% of the object manipulation; the trivial
    # free-phase object motion (<=12cm / <=39deg, post-carry net rotation <=3.1deg) is covered by the
    # always-on r_op/r_or. Margins are absolute (m) and IDENTICAL across sequences -> grading-identical-
    # config holds (the carry window differs only because the data differs). LIFT-based, NOT finger->object-
    # center distance: the center-distance contact proxy is not size-invariant (grip_radius 3.2/8.0/5.25cm
    # on seq1/2/3 -> a single threshold missed seq2's entire lift and fragmented seq3's rotation), whereas
    # lift-above-rest IS size-invariant and coincides exactly with "the object is being carried".
    carry_lift_lo = 0.005         # m: lift where carry starts ramping up (c=0 below)
    carry_lift_hi = 0.03          # m: lift where carry saturates (c=1 above); << every seq peak lift (13/14/27cm)

    # --- r_reach: object-anchored fingertip enclosure (2026-05-27) ---
    # Frame-0 dump (ep1500) showed WHY the grasp never forms: the hand tracks the MANO keypoints, which
    # follow the LIFTED reference object, so once the grip is missed it gets pulled UP into empty air and
    # abandons the grounded object (robot fingertips 9-13cm from the object vs MANO 1.7-2.9cm). r_grasp
    # can't bootstrap (its contact gate stays 0 — chicken/egg). FIX: a dense distance reward that pulls the
    # robot fingertips onto the ACTUAL object in the human grasp configuration. Target = actual obj_pos +
    # R(actual obj_rot) . (human fingertip offset expressed in the OBJECT's local frame), so it tracks
    # WHERE THE OBJECT REALLY IS and rotates WITH it through seq2/seq3's 180deg flips. Distance-based ->
    # non-zero gradient even meters away (unlike the contact gate), so it pulls the hand in; then friction
    # + r_op take over the lift. d measures deviation from the HUMAN fingertips, so it is object-SIZE
    # invariant. Identical for all 3 sequences; the target/offset are derived from each sequence's own data.
    # REBALANCE (2026-05-27): the first r_reach run pulled the fingertips 27cm->10cm toward the object but
    # STALLED at 10cm — w_reach=0.5 was too weak vs absolute fingertip tracking (r_ft, w=1.0, saturated
    # ~0.95) which pulls the fingers to the LIFTED reference keypoints in the air. So inside the grip window
    # we now (a) SUPPRESS r_ft and (b) run a much STRONGER r_reach, so committing the fingers to the ACTUAL
    # object wins. No grading loss: a correct grip puts the fingers on the lifted object = at the reference
    # keypoints, so r_reach and absolute tracking agree once lifted; the conflict only exists in the
    # failure state (object grounded). r_hand (21 kpts) still guides the overall hand pose.
    w_reach = 0.0                 # SUBSUMED by r_grip_pose (2026-05-30): r_grip_pose tracks the 5 tips +
                                  #   curl, so keeping r_reach(3) would DOUBLE-COUNT fingertip position
                                  #   (realized r_reach 1.18 + r_grip_pose 1.13 -> positional term dominates).
                                  # Path B v3 (2026-05-27): 2.0->3.0. Across fric+reach+pathB v1/v2 the
                                  #   fingertips asymptote ~3cm OUTSIDE the surface and never close the last
                                  #   gap (r_reach plateaus ~0.33, r_grasp=0, object untouched). Make this
                                  #   object-anchored drive dominate residual penalties/competing terms.
    reach_aggregation = "thumb_split_max"  # how r_reach/pose_gate_obj/r_close aggregate per-fingertip
                                  #   reach distance over the opposition sides (thumb vs the other 4).
                                  #   "thumb_split_max" (C2) = gate on the WORSE side, min(g_thumb,g_four):
                                  #   BOTH the thumb-side and the 4-finger-side must be near -> forces a
                                  #   simultaneous cage, the only state where enclosure (thumb x finger
                                  #   force) can fire. "thumb_split" (C1) = 50/50 sum, but one side alone
                                  #   earns 0.5 so the policy parked at "thumb in / 4 fingers 8cm out"
                                  #   (pa_v3: enclosure stayed 0, horizon stalled at 138). "worst" = max
                                  #   over all 5 fingers; "mean" = old 5-finger average that ignored the
                                  #   thumb entirely (pa_v2). See reach-penetration-collapses-grasp.
    reach_k = 20.0                # exp sharpness, d in meters: exp(-20*0.03)=0.55 at 3cm, ~1 when wrapped
    reach_penetration_frac = 0.25 # PROPORTIONAL penetration (2026-05-29): shorten each fingertip target
                                  #   toward the object center by this FRACTION of its own offset length,
                                  #   NOT an absolute distance. The old absolute reach_penetration=0.05m
                                  #   exceeded the per-fingertip offset for small objects and COLLAPSED all
                                  #   targets onto the object center (seq1: 92% collapse, target spread
                                  #   5.1cm->0.2cm; seq3: 20%; seq2: 0%) -- a single absolute value is NOT
                                  #   seq-agnostic. The collapse destroyed the opposition cage, so the hand
                                  #   only poked the near face and never lifted (pa_v1 frame-0 dump: lift 0,
                                  #   object knocked to rot 134deg). A fraction preserves each fingertip's
                                  #   direction and relative spread for ANY object size, and pushes deeper on
                                  #   bigger objects -> seq-agnostic. See memory reach-penetration-collapses-grasp.
    w_palmframe = 0.0             # DISABLED 2026-06-01 (pfm-revert): palmframe is a DEAD END. 3 runs
                                  #   (v1 dead / v2 dead / v3 grasp-recovered but frame-0 play FAILED to pour:
                                  #   airborne obj_rot 93deg, peak lift 5.7cm vs ref 13.2, grip distorted). The
                                  #   catch-22: pouring tilts the wrist -> enclosure drops -> palmframe(xenclosure)
                                  #   reward drops -> policy refuses to tilt = the grasp-saving gate blocks the pour.
                                  #   seq1's 135deg rotation = a wrist-tilt POUR; v6 solved it (11.9deg) with
                                  #   r_reach+r_or alone, NO grip_pose. Root cause = grip_pose over-constrains the
                                  #   ACTUAL-anchored upright hold (rotation-neutral). Revert to pure pfm and LOWER
                                  #   w_grip_pose so r_or drives the pour. See play-video-is-ground-truth.
                                  # NEW 2026-05-31: REFERENCE-anchored palm frame (wrist + 5 MCPs) = the
                                  #   rotation driver. grip_pose (distal, ACTUAL-anchored) holds the object but
                                  #   is satisfiable without rotating it (gp_cw_v1: tips 3cm yet wrist 9cm /
                                  #   palm 47deg off -> object under-rotated, rot 34deg vs v6 11.9deg). Tracking
                                  #   the palm frame to the object at the REFERENCE rotation forces the hand into
                                  #   the rotated pose -> rotates the held object, with a dense wrist-target
                                  #   gradient (vs r_or's outcome-only signal). Subsumes r_palm's anti-splay
                                  #   (ref==actual during approach). TUNE per result. 0.0 disables. seq-agnostic.
    w_palm = 0.7                  # RESTORED 2026-06-01 (anchor_v3): = pfm value. DISABLING it (anchor_v1/v2)
                                  #   was a mistake -- r_palmframe is REFERENCE-anchored so it does NOT subsume
                                  #   r_palm's ACTUAL-anchored root anti-splay (the dedicated palm-onto-the-real-
                                  #   object drive pfm relied on for contact; off -> splay/enclosure 0, gp_oppo).
                                  #   anchor_v2 (pfm grip_pose but w_palm=0) reproduced enclosure flat 0 -> the
                                  #   lost r_palm + the ungated reference palmframe both starved contact. Now
                                  #   r_palm restored AND r_palmframe enclosure-gated -> grip forms pfm-style first.
                                  # LOWERED 2026-05-31 (gp_full post-mortem): at 1.5 r_palm SATURATED to 0.95
                                  #   (palm err 2cm) and became the terminal local optimum — the policy parked
                                  #   the palm against the object and never closed the grip (enclosure flat ~0,
                                  #   r_grasp/r_hold=0 for 1100+ epochs). The contact-free reward plateau
                                  #   (r_hand+r_palm+r_grip_pose) out-paid the hard-to-reach grasp terms, so the
                                  #   policy rationally posed-without-gripping (pa_v6 lesson restated). Drop the
                                  #   palm reward's ABSOLUTE size below the grip-shaping terms so palm-near is no
                                  #   longer competitive with actually gripping, while keeping its anti-splay role.
                                  #   Single scalar -> trivially seq-identical (grading-identical-config holds).
                                  # RESTORED 2026-05-30: dedicated root-placement (anti-splay). gp_oppo (r_palm
                                  #   off, MCPs in r_grip_pose mean) splayed to 15cm aperture -> placement needs
                                  #   a DEDICATED weight, not 1/N dilution inside r_grip_pose's keypoint mean.
                                  # r_palm (2026-05-29, pa_v5): object-frame pull on the hand ROOT so the
                                  #   palm must approach the object instead of the policy splaying the
                                  #   fingers to reach with the palm held back (pa_v4 dump: palm 6cm too
                                  #   far, fingers 17 vs ref 12.7cm spread -> open poking hand, enclosure 0).
                                  #   Object-local target (drift-robust, no MANO-trap). 0.0 disables.
                                  #   < w_reach(3.0) so it positions the base without dominating fingertip reach.
    # Path B v3: finger-closure drive (proximity-gated). r_reach's distance term alone never induced the
    # actual CLOSING motion (fingers hover at a gap). Reward actuated-joint flexion ONLY when the fingertips
    # are near the object (so it closes ON the object, not a fist in mid-air) and inside the grip window.
    w_close = 1.0                 # RESTORED 2026-05-30: flexion drive. r_grip_pose (positions) doesn't force
                                  #   CLOSING (gp_oppo hit some tip targets with an OPEN splayed hand); r_close
                                  #   adds the curl drive once the palm is in (r_palm) and fingers are near.
    close_gate_k = 20.0           # exp sharpness of the proximity gate on mean fingertip->target distance
    # --- r_grip_pose (candidate, 2026-05-30): object-anchored FULL-finger grip configuration ---
    # Anchors all finger keypoints (MANO 1..20, wrist excluded) to the ACTUAL object and rewards matching
    # the human grip pose -> specifies the full 18-DOF finger curl (vs r_reach's 5 tips). PROBE: w=4.0 with
    # w_reach/w_palm/w_close=0 to isolate; verify err/grip_pose drops AND enclosure rises fast.
    w_grip_pose = 3.0             # RESTORED 2026-06-01 (or_linear) 2.0->3.0: the 3.0->2.0 lowering was REFUTED
                                  #   by dump (pfm_wg2 ep4200): loosening grip_pose did NOT fix the pour (axis
                                  #   still wrong, geodesic 126deg ~= anchor_v3's 130deg) AND regressed grip/lift
                                  #   (hand 7.7->9.9cm, airborne 133->124). grip_pose is rotation-NEUTRAL, so
                                  #   lowering it cannot tell the policy WHICH axis to rotate about -- the real
                                  #   fix is the r_or shape (or_linear), not grip_pose. Restore 3.0 for pfm's
                                  #   best-in-class grip quality. See memory rotation-wrong-axis-yaw.
                                  # 0.0 disables. 3.0 = inherits r_reach's role/magnitude (realized r_grip_pose
                                  #   @4 ~= r_reach @3; @3 keeps grip-shaping sum ~= object-tracking r_op+r_or
                                  #   so lift isn't crowded out — pa_v5 had shaping>tracking and under-lifted).
    grip_pose_k = 20.0            # exp sharpness, d in meters (same scale as reach_k).
    # LIFT-ONSET GRIP SHARPEN (2026-06-05, seq2 firm-grasp lever). Diagnosis (phasegrip ep3000 metrics):
    #   seq2's grasp is SAME-SIDE so enclosure(opposition)=0 AND its any-contact tail=0 (enclosure_ema 0.0001)
    #   -> r_grasp is structurally DEAD; the ONLY grip signal is r_grip_pose, which the policy satisfies with a
    #   LOOSE scoop (worst four-finger 13cm off) because exp(-20*d) still pays partial credit there -> the book
    #   is never firmly wrapped -> never lifts (actual_lift ~1.9cm). FIX: during the reference BREAK-OFF band
    #   (object just off the table, lift in [carry_lift_lo, ~2*gp_sharpen_lift_hi]) raise grip_pose_k so a loose
    #   grip's reward collapses and the lagging scoop finger is pulled in: k_eff = grip_pose_k*(1+gain*s[t]).
    #   GUARDRAIL: sharpens TRACKING of the object-anchored REFERENCE grip pose (imposes precision, NOT
    #   tightness) -> where the ref grip is loose (seq3 lift-onset, thumb-idx 6cm) it just demands precise-loose
    #   = benign. seq-agnostic: s[t] is a triangle on each seq's OWN reference lift height (verify below), so it
    #   peaks at break-off and is ZERO once steadily aloft -> seq3's solved 22cm hold/rotate (s=0 there) and
    #   seq1's solved pinch (already precise) are untouched; only seq2 (manipulates at 3-10cm) gets strong, broad
    #   coverage. NOT r_ft (suppressed in grip window; reviving it re-opened the contact-free MANO haven).
    gp_lift_sharpen = False       # REVERTED 2026-06-05: the lift-onset grip_pose-sharpen lever was FALSIFIED on
                                  #   seq2 (main_seq2_liftgate_v1): r_grip_pose PEAKED ~ep600 (0.20) then DECLINED
                                  #   to 0.115 while err/grip_pose WORSENED 0.05->0.13 and actual_lift plateaued at
                                  #   3.5cm. Root cause: grip_pose is finger-ANGLE imitation, not FORCE CLOSURE --
                                  #   the ref angles are matchable with fingertips OFF the surface (0 contact -> 0
                                  #   lift -> no r_hold return to hold the grip), so PPO drifts off it as mass anneals
                                  #   up. False = exact pre-lever behavior (k_eff == grip_pose_k everywhere); this is
                                  #   the config seq1(orlin)/seq3(massanneal) were validated under. Replaced by the
                                  #   contact-closure grip signal below ([[seq2-contact-closure-grip]]).
    gp_sharpen_gain = 1.0         # k_eff = grip_pose_k*(1+gain*s); s in [0,1] -> k up to 2x (20->~40) at break-off
    gp_sharpen_lift_hi = 0.05     # m: triangle peaks at this lift, decays to 0 by 2x (=10cm) << min seq peak (13cm)
    grip_pose_wfloor = 0.3        # PINKY-CURL FIX (2026-06-03, carry_v3): 0.2->0.3. carry_v1 frame-0 dump
                                  #   showed the non-contact PINKY curls inward (tip->wrist -2.2cm hold / -3.7cm
                                  #   release vs the ref which EXTENDS it; other fingers fine) -> floor 0.2
                                  #   under-constrains it. 0.3 = conservative bump (grasp-dilution-safer than 0.35,
                                  #   contact still ~3.3:1 dominant); if the pinky gap doesn't close, raise to 0.35.
                                  #   0.3 keeps contact points dominant (~3.3:1), far from
                                  #   gp_full's failed uniform 1.0 -> low grasp risk, seq-agnostic. floor's literal
                                  #   purpose IS non-contact finger pose, so this is the targeted lever.
                                  # WEIGHT FLOOR for the contact-proximity weighting (2026-05-31): the pure
                                  #   exp weights drove non-contact finger keypoints to ~0, leaving those
                                  #   fingers UNCONSTRAINED -> play video showed an ill-formed grip (some
                                  #   fingers curled, some extended, unnatural) that also can't execute a clean
                                  #   rotation. Floor each keypoint weight at this value so EVERY finger keeps a
                                  #   minimum pose constraint (natural hand + hand-matching score + a well-formed
                                  #   grip), while contact points still dominate (1.0 vs 0.2 = 5:1). 0.0 = pure
                                  #   exp (gp_cw_v1, sloppy fingers); 1.0 = uniform mean (gp_full, diluted contact).
                                  #   w_k = wfloor + (1-wfloor)*exp(-wbeta*(d_center-r_obj)). Single value -> seq-agnostic.
    grip_pose_wbeta = 30.0        # CONTACT-PROXIMITY weighting (2026-05-31): plain mean over all finger
                                  #   keypoints diluted the real contact points (fingertips) with palm-side
                                  #   MCP/PIP joints + fingers that don't grip in a given seq -> full-20
                                  #   r_grip_pose rewarded finger SHAPE without driving the tips INTO the
                                  #   object (gp_full/nohaven: enclosure ~0, vs r_reach's 0.26). Weight each
                                  #   kpt by exp(-wbeta*(d_center - r_obj)) where d_center = the HUMAN kpt's
                                  #   closest approach to the object center over the grip window and r_obj =
                                  #   the most-wrapped kpt's distance (~surface): points that WRAP the object
                                  #   weight ~1, points held off ~0. Data-derived per sequence under ONE rule
                                  #   (the wrap-set differs only because the demo differs) -> seq-agnostic,
                                  #   grading-identical-config holds. 30 = MCP knuckles (~3-6cm beyond surface)
                                  #   are down-weighted to ~0.2-0.4, non-grip fingers (~>6cm) ~0; tips+distal
                                  #   segments stay near 1 (keeps SHAPE, unlike r_reach's tip-only). d in m.
    # NOTE (2026-06-04): the carry_v4 object-tracking gate (track_tol/track_k) and the carry_v5 phase-aware
    # lift gate (gp_lift_floor) on r_grip_pose were both REVERTED. carry_v3 (ungated r_grip_pose, wfloor 0.3)
    # is the known-good config; the gates regressed the grasp. seq3 lift to be handled without gating this term.
    # PHASE-DEPENDENT grip weight (phasegrip, 2026-06-04): the reference grip DIFFERS between the lift phase
    # and the swirl/rotate phase (user observation on seq2). The contact-proximity weight (gp_kpt_weight) is a
    # SINGLE static vector built from min-over-window distances, so it demands EVERY wrapped finger for the
    # WHOLE window -> it fights the fingers the human RELEASES mid-swirl (seq2 ring/pinky). This makes the
    # weight per-frame, but RELEASE-ONLY: a finger's contact demand relaxes toward the pose floor ONLY on
    # frames where it leaves its OWN grip-peak by > phase_grip_release_dist; it can never demand MORE than the
    # static ratchet. Self-relative (each kpt vs its own window-min distance) -> seq-agnostic, size-independent,
    # grading-identical-config holds. VERIFIED on data: near-noop on seq1 (floored Δmean 0.003, all fingers
    # gate~1.00) and seq3 firm fingers (Δmean 0.020, thumb/index/middle/ring gate 0.91-1.00; pinky 0.86 =
    # the loose finger), ACTIVE on seq2 (pinky gate 0.19 in the swirl). ROLLBACK: phase_grip_weight=False
    # restores the exact static (K,) behavior (gate forced to 1). See memory phase-dependent-grip-weight.
    phase_grip_weight = False         # REVERTED (2026-06-05): wrong direction. It RELAXES a finger's grip demand
                                      #   when it leaves its grip-peak, but seq2's blocker is the OPPOSITE -- the
                                      #   initial lift needs a TIGHTER/more-precise grip at lift-onset (ref thumb-idx
                                      #   1.3cm @f91). near-noop on seq2 thumb anyway; phasegrip run plateaued at
                                      #   lift 1.6cm. Superseded by the lift-onset grip-sharpening lever.
                                      #   (False = exact pre-phasegrip static weight)
    phase_grip_release_dist = 0.04    # m a finger may leave its own grip-peak before its demand relaxes to floor
    phase_grip_k = 20.0               # sigmoid sharpness of the release gate (on the self-relative engagement)
    reach_pre_frames = 10         # dilate the grip window this many frames BEFORE liftoff so the closure
                                  #   incentive is present as the grip forms (not only once airborne)
    ft_grip_suppress = 1.0        # [0,1]: fraction of r_ft removed inside the grip window (1.0 = fully off
                                  #   there) so absolute fingertip tracking stops fighting r_reach. r_ft is
                                  #   untouched outside the grip window (approach/release).

    # --- Friction grasp bootstrap (2026-05-27, PERFORMANCE-GATED) ---
    # Open hand maxes r_hand/r_ft without touching the object, so r_op/r_or have no reachable gradient.
    # Temporarily raise the OBJECT friction so a clumsy grip (pulled in by r_reach) already lifts the
    # object -> r_op/r_or reachable -> grip gradient; then anneal friction back to nominal so the final
    # policy is valid at the grading physics (mu=1.0). Reward is untouched -> grading-identical-config
    # holds trivially. Object must still reach ref-z, so high friction can't be gamed by brushing.
    # SCHEDULE IS NOT EPOCH-BASED (a fixed epoch schedule is wrong: seq2/seq3 need far longer to learn the
    # grasp than seq1, so a fixed hold would pull the rug before they grip). Instead the anneal is gated on
    # forward-horizon PROGRESS: friction stays high until the horizon masters (near-)full trajectory, then
    # ratchets down by friction_step ONLY on batches where the policy still completes the trajectory w/o ET
    # at the current friction. Friction never gets ahead of the policy -> no rug-pull, no deadlock, and the
    # hold length + anneal rate auto-adapt per sequence with ONE identical rule (same pattern as the
    # fraction-based curriculum). If friction parks above nominal -> the task isn't yet learnable at nominal
    # (an informative signal). Training-only (`not self.play`); play/eval/grading run at obj_friction_nominal.
    # Decision + step happen in _update_horizon_curriculum; the value is
    # pushed to the sim in gr_env._apply_friction_anneal (called from _reset_idx).
    use_friction_anneal = True
    obj_friction_high = 5.0           # initial static=dynamic friction on the OBJECT. With sim-default hand
                                      #   friction 1.0 and PhysX "average" combine the effective hand<->object
                                      #   friction is ~ (5+1)/2 = 3.0 (kept <=~3 effective to avoid solver jitter).
    obj_friction_nominal = 1.0        # grading physics; the anneal lands here and play always uses this.
    friction_anneal_horizon_frac = 0.9  # only START lowering friction once the forward-horizon covers this
                                      #   fraction of the trajectory (= full task mastered at high friction).
                                      #   A FRACTION (not a frame count) -> sequence-agnostic over 250/510/660.
    friction_advance_thresh = 0.5     # lower friction a step only when >= this fraction of finishing envs
                                      #   complete the (near-)full trajectory WITHOUT early-termination at the
                                      #   current friction (the policy proves it can handle this level first).
    friction_step = 0.05              # friction units to drop per qualifying reset batch (5.0->1.0 = 80 steps),
                                      #   gated on success so it ratchets, never races ahead of the policy.
    # Friction-anneal gate REDESIGN (2026-05-28): the prior gate fired on horizon-completion + ET-free
    # advance, which is gameable by a hand-only-tracking policy (no grip needed). Result: friction reached
    # nominal at ep ~1500 for seq3 while r_grasp was still ~0.02 (grip never bootstrapped at high friction).
    # Replace with enclosure_ema gate: only anneal once the policy is ACTUALLY making contact (enclosure,
    # i.e., thumb+opposing contact force, is less diluted than r_grasp because it lacks the lift_gate and
    # pose_gate factors -> a robust seq-agnostic "is grip forming" signal). Safety: if the gate never fires,
    # force a single anneal step every friction_force_step_every reset batches so friction still reaches
    # nominal before training ends (eval/grading runs at obj_friction_nominal; a stuck-at-high policy can't
    # be evaluated). 5.0->1.0 needs 80 steps; with force_step_every=2000 the worst-case safety anneal
    # finishes in 160000 reset batches (~end of an 8000-epoch training at ~32 batches/epoch).
    friction_grip_ema_thresh = 0.40      # enclosure EMA threshold to TRIGGER anneal. RAISED 0.10->0.40
                                         #   (2026-05-30): at 0.10 the anneal fired on a mere TOUCH -- pa_v8
                                         #   made early contact (enclosure 0.28 @ep2000) which tripped the
                                         #   gate, friction crashed 4.85->1.0, and the still-immature partial
                                         #   pinch lost the lift crutch before it could bear weight -> froze
                                         #   at a "weird grip" (thumb+1 finger, others splayed, no lift).
                                         #   0.40 keeps friction high until the grip is FIRM (v5 reached 0.65
                                         #   under a sustained crutch), so the grip matures + lifts before the
                                         #   crutch is removed, then anneals to nominal for grading.
    friction_force_step_every = 2000     # force one anneal step every N reset batches if gate hasn't fired
                                          #   (safety so friction reaches nominal even on stuck runs)

    # --- Object-MASS anneal (SCOOP bootstrap, 2026-06-04) ---
    # The friction anneal is the crutch for a PINCH (high friction stops the object slipping out of an
    # opposition grip). It CANNOT bootstrap a same-side SCOOP: seq3 lifts the book with the 4 fingers
    # tucked UNDER it, and pressing on/beside a heavy book transmits no vertical force no matter the
    # friction (zlift_v1 PROOF: obj_friction stuck at 4.7, enclosure 0.82, yet actual_lift 0 -> the
    # policy is physically wedged in a non-liftable same-side press, see [[grasp-topology-pinch-vs-scoop]]).
    # The MASS crutch fixes exactly this: start the object LIGHT so the book RESPONDS to even a partial,
    # clumsy under-purchase (a heavy book ignores a glancing under-touch -> zero reward gradient; a light
    # one visibly rises -> gradient). The policy discovers "get a little under + raise -> book follows",
    # the horizon advances through the lift wall, and then mass is ratcheted back to nominal ONLY on
    # batches where the policy STILL completes the trajectory without ET -> the grip must mature to bear
    # the real weight (identical progress-gated, no-rug-pull rule as the friction anneal; never races
    # ahead of the policy). The object must still reach the reference z, so a light mass can't be gamed by
    # brushing. Mass is a per-object SCALE of each sequence's own USD nominal -> grading-identical config
    # holds. Training-only; play/eval/grading always run at the nominal USD mass (like friction).
    # FALSIFIABLE: if the horizon advances under light mass but COLLAPSES as mass anneals up, the policy
    # learned a ballistic flick, not a grip -> the ET-on-trajectory-divergence should already block that
    # (a flicked book leaves the smooth ref path), but if it doesn't, revisit with a hold-duration gate.
    use_mass_anneal = True
    obj_mass_low_frac = 0.15          # start mass = 15% of the USD nominal (heavy book -> light, liftable
                                      #   by a clumsy partial scoop so the lift gets a reward gradient).
    obj_mass_nominal_frac = 1.0       # anneal TARGET (grading mass); play always uses the USD nominal mass.
    mass_anneal_horizon_frac = 0.9    # only START raising mass once the horizon covers this fraction of the
                                      #   trajectory (full motion mastered under the light crutch). A FRACTION
                                      #   (not a frame count) -> sequence-agnostic over 250/510/660.
    mass_advance_thresh = 0.5         # raise mass a step only when >= this fraction of finishing envs complete
                                      #   the (near-)full trajectory WITHOUT ET at the current mass.
    mass_step_frac = 0.02             # mass-fraction ADDED per qualifying reset batch (0.15->1.0 = ~43 steps),
                                      #   gated on success so it ratchets up, never ahead of the policy.
    mass_grip_ema_thresh = 0.40       # enclosure EMA to TRIGGER the ramp (same robust "grip forming" signal
                                      #   the friction gate uses; keeps the crutch until the grip is firm).
    # SCOOP grip-gate (2026-06-05): the mass grip_learned gate reads enclosure_ema, which is OPPOSITION-based
    # and ~0 for seq2/seq3 SAME-SIDE scoops -> the gate NEVER fires there, so mass only crawls via the safety
    # timer and stalls (seq2 main_seq2_contact_v1: mass stuck 0.48 -> policy never trained at nominal mass ->
    # frame-0 play could not lift the full-mass book: 0/660 airborne). FIX (_grip_learned): when opposition is
    # ABSENT (scoop), gate on contact_closure_ema instead. PROVABLY seq1-NEUTRAL: seq1's pinch keeps
    # opposition_ema high (> opp_absent_thresh) so the scoop branch is DISABLED and the gate stays byte-identical
    # to enclosure_ema > mass_grip_ema_thresh. seq2/seq3 (opposition~0) take the contact branch. The mass ratchet
    # is still ANDed with horizon_done + advance_ok, so mass self-throttles to the policy's capability (it only
    # rises while the policy keeps completing the trajectory at the current mass). [[seq2-contact-closure-grip]]
    use_scoop_grip_gate = True
    # Scoop signature = "real multi-finger contact AND opposition far below it". RATIO discriminator (not an
    # absolute opp threshold) so it is magnitude/stage-independent: for a PINCH the thumb is among the top-2
    # contacts, so contact_closure(top-2 product) == opposition(thumb x max_other) EXACTLY -> opposition is
    # NEVER < opp_scoop_frac*contact_closure -> seq1's scoop branch is PROVABLY always False at every grip
    # strength and training stage (gate stays byte-identical to enclosure_ema > thresh). Only a SAME-SIDE grip
    # (thumb NOT in the top-2, seq2/seq3) drives opposition << contact_closure and activates the branch.
    mass_grip_contact_thresh = 0.03   # contact_closure_ema above this = real multi-finger contact forming.
    opp_scoop_frac = 0.5              # opposition_ema < this * contact_closure_ema => genuine scoop (no pinch).
    mass_force_step_every = 2000      # safety: force one step every N reset batches if the gate never fires,
                                      #   so mass reaches nominal before training ends (grading runs at nominal).

    def __post_init__(self):
        super().__post_init__()
        for finger in self.fingertip_body_names:
            setattr(
                self.scene,
                f'contact_sensor_{finger}',
                ContactSensorCfg(
                    prim_path=f'{{ENV_REGEX_NS}}/Robot/{finger}',
                    update_period=0.0,
                    history_length=6,
                    filter_prim_paths_expr=["{ENV_REGEX_NS}/Object"],
                ),
            )
