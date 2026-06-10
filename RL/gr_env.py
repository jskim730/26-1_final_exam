# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations
import numpy as np
import torch
import torch.nn.functional as F
from collections.abc import Sequence

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs import DirectRLEnv
from isaaclab.markers import VisualizationMarkers
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import axis_angle_from_quat, quat_conjugate, quat_from_angle_axis, quat_mul, quat_apply, saturate, matrix_from_quat, quat_from_matrix, euler_xyz_from_quat, quat_from_euler_xyz
from .gr_env_cfg import GrEnvCfg
from pxr import Usd, UsdPhysics
import omni.usd


class GrEnv(DirectRLEnv):
    cfg: GrEnvCfg

    def __init__(self, cfg: GrEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self.inputs = torch.load(cfg.seq_ref_path, map_location="cpu")

        self.num_hand_dof = self.hand.num_joints

        self.num_kpts = len(self.cfg.MANO_kpts)
        self.termination = not self.cfg.play
        self.play = self.cfg.play
        self.time_out = torch.zeros((self.num_envs, ), device=self.device).bool()
        self.episode_length = self.cfg.episode_length

        # list of joints, hand_bodies, fingertip_bodies, root, rigid bodies
        self.actuated_dof_indices = list()
        self.root_body = list()
        self.hand_bodies = list()
        self.hand_body_names = list()
        self.fingertip_bodies = list()

        for joint_name in self.cfg.actuated_joint_names:
            self.actuated_dof_indices.append(self.hand.joint_names.index(joint_name))
        for i in range(len(self.hand.data.body_names)):
            if self.hand.data.body_names[i] != 'robot0_hand_mount':
                self.hand_body_names.append(self.hand.data.body_names[i])
                self.hand_bodies.append(i)
                if self.hand.data.body_names[i] == 'robot0_palm':
                    self.root_body.append(i)
        for body_name in self.cfg.fingertip_body_names:
            self.fingertip_bodies.append(self.hand_body_names.index(body_name))
        
        # num of joints, hand_bodies, fingertip_bodies, rigid bodies
        self.num_actuated_dof = len(self.actuated_dof_indices)
        self.num_hand_bodies = len(self.hand_bodies)
        self.num_fingertips = len(self.fingertip_bodies)
        
        # ref parameters
        self.hand_pos_ref = torch.zeros((self.num_envs, 3), device=self.device)
        self.hand_rot_ref = torch.zeros((self.num_envs, 4), device=self.device)
        self.hand_dof_ref = torch.zeros((self.num_envs, self.num_hand_dof), device=self.device)
        self.obj_pos_ref = torch.zeros((self.num_envs, 3), device=self.device)
        self.obj_rot_ref = torch.zeros((self.num_envs, 4), device=self.device)
        self.hand_rot_ref[:,0] = 1.0
        self.obj_rot_ref[:,0] = 1.0

        # object parameters
        self.obj_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.obj_rot = torch.zeros((self.num_envs, 4), device=self.device)
        self.obj_linvel = torch.zeros((self.num_envs, 3), device=self.device)
        self.obj_angvel = torch.zeros((self.num_envs, 3), device=self.device)
        self.obj_pos_reset = torch.zeros((self.num_envs, 3), device=self.device)
        self.obj_rot_reset = torch.zeros((self.num_envs, 4), device=self.device)
        self.obj_rot_reset[:,0] = 1.0

        # hand parameters
        self.hand_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.hand_rot = torch.zeros((self.num_envs, 4), device=self.device)
        self.hand_linvel = torch.zeros((self.num_envs, 3), device=self.device)
        self.hand_angvel = torch.zeros((self.num_envs, 3), device=self.device)
        self.hand_pos_reset = torch.zeros((self.num_envs, 3), device=self.device)
        self.hand_rot_reset = torch.zeros((self.num_envs, 4), device=self.device)
        self.hand_rot_reset[:,0] = 1.0
        self.hand_dof_pos_reset = torch.zeros((self.num_envs, self.num_hand_dof), device=self.device)
        self.hand_dof_pos = torch.zeros((self.num_envs, self.num_hand_dof), device=self.device)
        self.hand_dof_vel = torch.zeros((self.num_envs, self.num_hand_dof), device=self.device)

        self.hand_bodies_pos = torch.zeros((self.num_envs,self.num_hand_bodies,3), device=self.device)
        self.hand_bodies_rot = torch.zeros((self.num_envs,self.num_hand_bodies,4), device=self.device)
        self.hand_bodies_linvel = torch.zeros((self.num_envs,self.num_hand_bodies,3), device=self.device)
        self.hand_bodies_angvel = torch.zeros((self.num_envs,self.num_hand_bodies,3), device=self.device)

        self.hand_kpts_pos = torch.zeros((self.num_envs, self.num_kpts, 3), device=self.device)

        # fingertip parameters
        self.fingertip_pos = torch.zeros((self.num_envs,self.num_fingertips,3), device=self.device)
        self.fingertip_normal = torch.zeros((self.num_envs,self.num_fingertips,3), device=self.device)
        self.fingertip_normal[:, 1:, 1] = -1
        self.fingertip_normal[:, 0, 0] = -1
        self.fingertip_rot = torch.zeros((self.num_envs,self.num_fingertips,4), device=self.device)
        self.fingertip_linvel = torch.zeros((self.num_envs,self.num_fingertips,3), device=self.device)
        self.fingertip_angvel = torch.zeros((self.num_envs,self.num_fingertips,3), device=self.device)

        # body to keypoints
        self.fingertip_offset = torch.zeros((self.num_envs,self.num_fingertips,3), device=self.device)
        self.fingertip_offset[:, 0, :] = torch.tensor([-0.0085, 0.0, 0.02], device=self.device)
        self.fingertip_offset[:, 1, :] = torch.tensor([0.0, -0.006, 0.0175], device=self.device)
        self.fingertip_offset[:, 2, :] = torch.tensor([0.0, -0.006, 0.0175], device=self.device)
        self.fingertip_offset[:, 3, :] = torch.tensor([0.0, -0.006, 0.0175], device=self.device)
        self.fingertip_offset[:, 4, :] = torch.tensor([0.0, -0.006, 0.0175], device=self.device)

        # fingertip force
        self.fingertip_contact_forces = torch.zeros((self.num_envs, self.num_fingertips,3), device=self.device)
        self.fingertip_contact_forces_buf = torch.zeros((self.num_envs, 3, self.num_fingertips), device=self.device)

        # joint limits
        joint_pos_limits = self.hand.root_physx_view.get_dof_limits().to(self.device)
        self.hand_dof_lower_limits = joint_pos_limits[..., 0]
        self.hand_dof_upper_limits = joint_pos_limits[..., 1]

        # delta
        self.delta_obj_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.delta_fingertip_pos = torch.zeros((self.num_envs, self.num_fingertips), device=self.device)
        
        # delta_value
        self.delta_obj_pos_value = torch.zeros((self.num_envs, ), device=self.device)

        # frame idx
        self.start_frame_idx = torch.zeros(self.num_envs, dtype=torch.int, device=self.device)
        self.sampled_frame_idx = torch.zeros(self.num_envs, dtype=torch.int, device=self.device)

        # buffer for full policy action (pos3 + rot6d + finger18); init zero so first obs is valid
        self.actions = torch.zeros((self.num_envs, self.cfg.action_space), dtype=torch.float, device=self.device)
        # buffers for dof actions
        self.prev_dof_actions = torch.zeros((self.num_envs, self.num_hand_dof), dtype=torch.float, device=self.device)
        self.cur_dof_actions = torch.zeros((self.num_envs, self.num_hand_dof), dtype=torch.float, device=self.device)
        # buffers for external force and torque
        self.prev_forces = torch.zeros((self.num_envs, 3), dtype=torch.float, device=self.device)
        self.prev_torques = torch.zeros((self.num_envs, 3), dtype=torch.float, device=self.device)
        # track goal resets
        self.hand_far_apart = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.obj_far_apart = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.early_terminate = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

        # markers
        self.goal_markers = VisualizationMarkers(self.cfg.goal_marker_cfg)
        self.debug_markers = VisualizationMarkers(self.cfg.debug_marker_cfg)
        
        # separate reward logging
        self.logs_dict = dict()

        # track successes
        self.successes = torch.zeros(self.num_envs, dtype=torch.float, device=self.device)
        self.consecutive_successes = torch.zeros(1, dtype=torch.float, device=self.device)

        # global action
        self.is_global = True

        self._setup_data()

        # --- RSI/ET derived quantities (depend on the sequence data set up above) ---
        # Reference trajectory length (number of frames).
        self.seq_len = self.obj_pos_seq.shape[0]
        # Rigid palm<->MANO-wrist offset measured at frame 0. The data has no per-frame robot
        # hand pose, so for RSI we re-use this offset to place the palm relative to the MANO
        # wrist (keypoint 0) at any sampled start frame.
        self.hand_root_to_wrist = self.hand_pos_reset[0].clone() - self.mano_kpts_pos_seq[0, 0]
        # Palm (hand-root) object-frame target offset, for r_palm (2026-05-29, pa_v5). Built HERE (after
        # hand_root_to_wrist, which needs hand_pos_reset finalized in _setup_data) not inside _setup_data.
        # pa_v4 dump: the policy satisfies the fingertip-only r_reach by SPLAYING the fingers and keeping
        # the palm ~6cm too far back (robot wrist->obj 18cm vs ref 11.7cm, spread 17 vs 12.7cm) -> open
        # poking hand, no cage, enclosure 0. r_palm pulls the hand root to where it should be so the palm
        # comes IN and the fingers close without splaying. OBJECT-LOCAL (like the fingertip offsets) -> it
        # rotates with the ACTUAL object -> drift-robust across seq2/seq3 rotations, unlike absolute r_ft
        # (which would re-introduce the MANO-trap on high-drift seqs). root target = MANO wrist offset
        # (kpt 0) + rigid frame-0 root<->wrist vector (same approximation the RSI reset uses).
        _root_off_world = self.obj_kpts_pos_seq_offset[:, 0] + self.hand_root_to_wrist   # (T,3) root rel obj, world
        self.obj_palm_offset_local = quat_apply(quat_conjugate(self.obj_rot_seq), _root_off_world)  # (T,3) obj-local
        # --- Reference rotation AXIS + angle relative to frame 0 (for or_axis_align swing term, 2026-06-08) ---
        # The swing-twist axis-purity term needs the reference rotation axis at each frame. Precompute once here
        # from the relative quaternion q_rel = q_seq[t] * q_seq[0]^-1 (world frame). The quaternion axis
        # (xyz/|xyz|) is STABLE at theta=180deg (w->0, xyz->unit) -- unlike the matrix (R-R^T) axis which
        # vanishes there, exactly where seq2/seq3 flip. It is ill-defined only at theta~0, which the magnitude
        # gate (ref_rot_angle/pi) zeroes out. Object-only -> grip-safe; data-given axis -> seq-agnostic.
        _q0 = self.obj_rot_seq[0:1].expand_as(self.obj_rot_seq)              # (T,4)
        _qrel = quat_mul(self.obj_rot_seq, quat_conjugate(_q0))             # (T,4) rotation from frame 0
        _xyz = _qrel[:, 1:]
        _nrm = torch.norm(_xyz, dim=-1, keepdim=True)
        self.ref_rot_axis = _xyz / _nrm.clamp_min(1e-8)                    # (T,3) unit (sign-free in swing use)
        self.ref_rot_angle = 2.0 * torch.atan2(_nrm.squeeze(-1), _qrel[:, 0].abs())   # (T,) 0..pi
        # --- Reference grasp TOPOLOGY: pinch (opposition cage) vs scoop (same-side), 2026-06-08 ---
        # ([[seq2-horizon-deadlock]], fixes the lift_gate_bootstrap_all blanket that broke seq1.) The live
        # _is_scoop() needs contact_closure_ema -> chicken-egg: seq2's contact never forms until the horizon
        # passes the grasp frames, but the horizon won't advance until it's recognized as a scoop. So the
        # bootstrap bypass was widened to ALL topologies (lift_gate_bootstrap_all), which ALSO disabled the
        # lift-gate for seq1's PINCH during the long light-mass ramp -> reopened seq1's no-lift exploit.
        # Decide the topology from the DEMO GEOMETRY instead, available before any contact: over the carry
        # window, side-cos(obj-center -> thumb_tip, obj-center -> finger_tip). cos<0 on ANY finger = thumb
        # opposes a finger = squeezing cage = PINCH (seq1). All cos>0 = SAME-SIDE scoop (seq2/seq3). VERIFIED
        # separation (verify_seq2_enclosure.py): opposition-frame fraction seq1=100% vs seq2/seq3=0%, so the
        # 0.5 threshold has the largest possible margin. Data-driven -> seq-agnostic / byte-identical: the
        # same code lets the reference decide the topology. obj_fingertip_pos_seq_offset is to_center-invariant
        # (object and MANO are shifted by the same to_center_pos), so this matches the verify script exactly.
        _off = self.obj_fingertip_pos_seq_offset                          # (T,5,3) tip rel obj-center; idx0=thumb
        _lift = self.obj_pos_seq[:, 2] - self.obj_pos_seq[0, 2]           # (T,) lift height vs frame 0
        _craw = ((_lift - 0.005) / (0.03 - 0.005)).clamp(0.0, 1.0)        # carry ramp (same as verify script)
        _cb = _craw.clone()
        for _s in range(1, 11):                                           # dilate 10 frames forward
            _cb[:-_s] = torch.maximum(_cb[:-_s], _craw[_s:])
        _carry = _cb > 0.5
        if int(_carry.sum()) < 1:
            _carry = torch.ones_like(_carry)                             # fallback: object never airborne
        _vv = _off[_carry]                                               # (C,5,3)
        _vv = _vv / _vv.norm(dim=-1, keepdim=True).clamp_min(1e-6)       # unit dirs from obj center
        _cos = torch.einsum("ck,cfk->cf", _vv[:, 0], _vv[:, 1:])         # (C,4) cos(thumb, finger_k)
        self.ref_opp_frac = float((_cos.min(dim=1).values < 0).float().mean())   # frames w/ ANY opposition
        self._ref_is_scoop = self.ref_opp_frac < self.cfg.ref_scoop_opp_frac_thresh
        print(f"[GrEnv] ref grasp topology: opp_frac={self.ref_opp_frac:.3f} -> "
              f"{'SCOOP (lift-gate bootstrap bypass ON)' if self._ref_is_scoop else 'PINCH (lift-gate kept)'}")
        # Forward-horizon curriculum: max steps an episode may run from frame 0, grown one-sided
        # as the policy masters the current frontier (see _update_horizon_curriculum).
        self.horizon = float(self.cfg.horizon_init)
        # CURRICULUM LIFT-GATE accumulators (2026-06-06): per-env running sums over the current episode of
        # the lift DEMAND (un-dilated ref-lift ramp) and demand-weighted lift_track. Their ratio at reset =
        # demand-weighted mean lift adequacy, used in _update_horizon_curriculum to gate `advance` on real
        # lift. Demand-sum ~0 (approach-only horizon, no lift demanded yet) -> the env passes freely.
        self._ep_demand_sum = torch.zeros(self.num_envs, device=self.device)
        self._ep_lt_wsum = torch.zeros(self.num_envs, device=self.device)
        # Friction grasp bootstrap (performance-gated): current object friction, ratcheted high->nominal in
        # the forward-horizon curriculum as the policy masters the trajectory (see
        # _update_horizon_curriculum). _friction_applied = last value pushed to the sim.
        # Training-only; play never touches the material, so it keeps the nominal sim-default friction.
        self.obj_friction = float(self.cfg.obj_friction_high)
        self._friction_applied = None

        # Object-MASS anneal (SCOOP bootstrap, 2026-06-04): friction can't lift a same-side scoop, so start
        # the object LIGHT (obj_mass_frac of the USD nominal) and ratchet the fraction up to 1.0 in
        # _update_horizon_curriculum on the SAME progress gate as friction. obj_mass_nominal is captured
        # lazily from the sim on the first _apply_mass_anneal (before any override). _mass_applied = last
        # fraction pushed to the sim. Training-only; play keeps the nominal USD mass. See cfg block.
        self.obj_mass_frac = float(self.cfg.obj_mass_low_frac)
        self.obj_mass_nominal = None
        self._mass_applied = None
        self._mass_idle_batches = 0

        # Path B v6 (2026-05-27): regularization anneal. Smoothness penalties (action/dof) suppress the
        # exploratory finger motion needed to DISCOVER the grasp from scratch, so a fresh run with the full
        # (smooth) reg never grips. Start the reg at reg_anneal_start_mult of its final value (low -> grasp
        # discovery works, as in v3/v5), then ratchet reg_mult->1.0 once the grasp is ESTABLISHED (EMA of
        # r_grasp > reg_anneal_grasp_thresh) to smooth the final motion. Grasp-gated => seq-agnostic (adapts
        # to when each sequence learns to grip). reg_mult multiplies action/dof penalty scales in _get_rewards.
        self.reg_mult = float(self.cfg.reg_anneal_start_mult)
        self.grasp_ema = 0.0
        self.last_r_grasp = torch.zeros(self.num_envs, device=self.device)
        # Friction-anneal redesign (2026-05-28): track enclosure EMA (less diluted than r_grasp; see cfg
        # friction_grip_ema_thresh) and a safety counter so friction reaches nominal even if the gate
        # never fires. Logged each reset batch as curriculum/enclosure_ema + curriculum/friction_idle.
        self.enclosure_ema = 0.0
        self.last_enclosure = torch.zeros(self.num_envs, device=self.device)
        # SCOOP grip-gate (2026-06-05): opposition_ema discriminates pinch (seq1, high) vs scoop (seq2/3, ~0);
        # contact_closure_ema is the opposition-free grip signal that feeds the scoop branch of _grip_learned.
        self.opposition_ema = 0.0
        self.last_opposition = torch.zeros(self.num_envs, device=self.device)
        self.contact_closure_ema = 0.0
        self.last_contact_closure = torch.zeros(self.num_envs, device=self.device)
        self._friction_idle_batches = 0


    def _setup_data(self):
        # Provided code. Do not modify.
        obj_bottom_offset = self.inputs['obj_bottom_offset'].to(self.device)
        obj_reset_pos = torch.zeros((1,3), dtype=torch.float, device=self.device)
        obj_reset_pos[0][2] = self.cfg.table_upper_z + obj_bottom_offset - 0.001
        obj_trans = self.inputs['obj_trans'].to(self.device)
        obj_rot = self.inputs['obj_rot'].to(self.device)
        obj_rot = quat_from_matrix(obj_rot)
        to_center_pos = (- obj_trans[0:1] + obj_reset_pos)

        self.obj_rot_reset[:] = obj_rot[0]
        self.obj_rot_seq = obj_rot
        self.obj_pos_seq = obj_trans + to_center_pos
        self.obj_linvel_seq = self.inputs['obj_vel'].to(self.device)
        self.obj_angvel_seq = self.inputs['obj_angvel'].to(self.device)
        self.obj_linvel_value_seq = torch.norm(self.obj_linvel_seq, p=2, dim=-1)
        self.obj_angvel_value_seq = torch.norm(self.obj_angvel_seq, p=2, dim=-1)
        
        mano_kpts_pos_seq = self.inputs["mano_kpts"][:, self.cfg.MANO_kpts].to(self.device)
        self.mano_kpts_pos_seq = mano_kpts_pos_seq + to_center_pos.unsqueeze(1)
        self.fingertip_pos_seq = self.mano_kpts_pos_seq[:, self.cfg.MANO_fingertips]
        

        self.obj_kpts_pos_seq_offset =  self.mano_kpts_pos_seq - self.obj_pos_seq.unsqueeze(1)
        self.obj_fingertip_pos_seq_offset = self.obj_kpts_pos_seq_offset[:, self.cfg.MANO_fingertips]

        # r_reach precompute: express the human fingertip->object offsets in the OBJECT's LOCAL frame so the
        # grasp pose can be re-anchored to the ACTUAL object pose each step and rotates WITH the object
        # through seq2/seq3's 180deg flips. off_world (T,F,3) -> off_local (T,F,3) via inverse ref rotation.
        _T, _F = self.obj_fingertip_pos_seq_offset.shape[:2]
        _q = self.obj_rot_seq.unsqueeze(1).expand(_T, _F, 4).reshape(-1, 4)
        self.obj_fingertip_offset_local = quat_apply(
            quat_conjugate(_q), self.obj_fingertip_pos_seq_offset.reshape(-1, 3)
        ).reshape(_T, _F, 3)
        # Penetration target (PROPORTIONAL, 2026-05-29): shorten each fingertip offset toward the object
        # center by a FRACTION of its own length so the r_reach target sits inside the surface (rewards a
        # press, not a hover). The earlier ABSOLUTE subtraction (reach_penetration=0.05m) exceeded the
        # per-fingertip offset for small objects and collapsed every target onto the object center (seq1:
        # 92% of targets, spread 5.1cm->0.2cm), so r_reach pulled all 5 fingertips to one point -> the hand
        # could only poke the near face and never formed a liftable opposition cage (pa_v1 frame-0: lift 0).
        # A proportional push preserves each fingertip's direction and relative spread for ANY object size
        # (deeper on bigger objects) -> seq-agnostic. See memory reach-penetration-collapses-grasp.
        self.obj_fingertip_offset_local = self.obj_fingertip_offset_local * (1.0 - self.cfg.reach_penetration_frac)
        # r_grip_pose precompute: object-LOCAL offsets for ALL 21 MANO keypoints (full hand pose), so the
        # human grip CONFIGURATION can be re-anchored to the actual object each step (same construction as
        # the fingertip offsets above, extended to all keypoints, NO penetration -> match the human pose).
        _Tk, _K = self.mano_kpts_pos_seq.shape[:2]
        _qk = self.obj_rot_seq.unsqueeze(1).expand(_Tk, _K, 4).reshape(-1, 4)
        self.obj_kpt_offset_local = quat_apply(
            quat_conjugate(_qk), self.obj_kpts_pos_seq_offset.reshape(-1, 3)
        ).reshape(_Tk, _K, 3)
        # ANCHOR SPLIT (2026-05-31): the hand has two jobs needing DIFFERENT target anchors.
        #  (1) DISTAL finger keypoints (PIP/DIP/TIP of every finger) HOLD the object -> anchor to the
        #      ACTUAL object pose (must track where the object really is, else they grab air). -> grip_pose.
        #  (2) PALM FRAME (wrist + the 5 MCP knuckles) ORIENTS the hand. The gross hand orientation is what
        #      rotates a grasped object, so anchor it to the object at the REFERENCE rotation -> matching it
        #      REQUIRES the object to rotate to the reference (-> r_palmframe below). The old single grip_pose
        #      (all 1..20, ACTUAL-anchored) was fully satisfiable WITHOUT rotating, so the object under-rotated
        #      (gp_cw_v1 dump: tips 3cm but wrist 9cm / palm 47deg off). MCPs are MOVED to the palm frame,
        #      NOT dropped (the 2026-05-30 distal-only run splayed because nothing held the palm) -- the
        #      reference palm frame holds them (ref==actual during approach -> same anti-splay; the anchors
        #      differ only once rotation is demanded). Finger block layout [MCP,PIP,DIP,TIP], dist-from-wrist monotone.
        # anchor_v2 (2026-06-01): grip_pose keeps ALL finger kpts incl MCPs (= proven pfm grip generator).
        # The distal-only split (anchor_v1) removed the MCPs that pin the finger BASES onto the ACTUAL object
        # -> palm never pressed in -> enclosure 0 / claw-in-air (memory line 95 warning realized: ep2655
        # enclosure 0.0000 vs pfm 0.80, err/grip_pose identical 6cm = shape mimicked off the object). MCPs are
        # NOT moved out; they stay actual-anchored HERE (contact/anti-splay) AND ALSO appear in r_palmframe
        # below (reference-anchored, rotation driver). The overlap is intended: approach ref~=actual (no
        # conflict), the two anchors diverge only in the rotate phase -> the wanted rotation tension on the palm.
        self.grip_pose_kpts = [i for i in range(_K) if i != 0]                     # all finger kpts (= pfm)
        self.palmframe_kpts = [0, 1, 5, 9, 13, 17]                                 # wrist + 5 MCPs (rotation frame)
        # Opposition split for r_grip_pose: thumb (finger block 1 = kpts 1..4 incl MCP) vs the other 4
        # fingers (kpts 5..20). Gate on the WORSE side so the THUMB must match -- a plain mean under-weights
        # the thumb and the policy satisfies it with the 4 fingers while the thumb drifts -> no opposition
        # cage. Positions into the grip_pose_kpts-ordered distance tensor.
        self.gp_thumb_mask = [j for j, k in enumerate(self.grip_pose_kpts) if k in (1, 2, 3, 4)]
        self.gp_four_mask = [j for j, k in enumerate(self.grip_pose_kpts) if k >= 5]
        # Per-finger keypoint groups (positions in grip_pose_kpts order) for the four non-thumb fingers
        # (index 5-8 / middle 9-12 / ring 13-16 / pinky 17-20). r_grip_pose gates the four side on the
        # WORST finger so EACH finger the demo uses must reach its wrap target -- the old 16-kpt mean let
        # one finger (e.g. index) be averaged away by the others -> thumb-side pinch, no full 4-finger
        # wrap (2026-05-31, observed in gp_cw_v1 play video). Same worst-side logic as thumb-vs-four,
        # one level deeper.
        self.gp_finger_masks = [
            [j for j, k in enumerate(self.grip_pose_kpts) if base <= k <= base + 3]
            for base in (5, 9, 13, 17)
        ]
        # Carry phase signal c[t] (verified lift-based, 2026-06-03): the object is being CARRIED when the
        # reference object is airborne. SMOOTH ramp on the reference lift height above the frame-0 rest,
        # backward-dilated by reach_pre_frames so grip formation just before liftoff already counts as carry.
        # carry_seq is the phase weight that gates every carry-added grip term and the absolute-fingertip
        # suppression ("free = always-on base, carry = base + c*grip"). Replaces the previous BINARY grip
        # window with a smooth blend -> continuous gradient at the approach<->carry<->release transitions.
        # Verified seq-agnostic (verify_carry_lift.py): a single contiguous carry block on all 3 sequences,
        # bracketing >99% of the object manipulation; the trivial free-phase object motion is covered by the
        # always-on r_op/r_or. LIFT-based, NOT finger->object-center distance: the center-distance proxy is
        # not size-invariant (grip_radius 3.2/8.0/5.25cm on seq1/2/3 -> a single threshold missed seq2's whole
        # lift and fragmented seq3's rotation), whereas lift-above-rest is size-invariant. See cfg.carry_lift_*.
        _z_rest = self.obj_pos_seq[0, 2]
        _lift_ref = self.obj_pos_seq[:, 2] - _z_rest                                        # (T,)
        _carry_raw = ((_lift_ref - self.cfg.carry_lift_lo) /
                      (self.cfg.carry_lift_hi - self.cfg.carry_lift_lo)).clamp(0.0, 1.0)
        _carry = _carry_raw.clone()
        for _s in range(1, int(self.cfg.reach_pre_frames) + 1):
            _carry[:-_s] = torch.maximum(_carry[:-_s], _carry_raw[_s:])  # backward dilation -> grip forms
        self.carry_seq = _carry                                                             # (T,) in [0,1]
        # Lift-onset grip-sharpen weight s[t] (2026-06-05, seq2 firm-grasp lever; see cfg.gp_lift_sharpen).
        # Triangle on the reference lift height: 0 on the table, peaks at gp_sharpen_lift_hi (break-off /
        # early ascent where the firm wrap must form), decays to 0 by 2*hi (well aloft). Self-normalized on
        # each seq's OWN lift -> seq-agnostic; ZERO during a steady high-altitude hold (seq3 rotate) so it
        # cannot disturb seq3's solved lift. Reference-only (per-frame scalar, broadcast over envs).
        _hi = float(self.cfg.gp_sharpen_lift_hi)
        _up = ((_lift_ref - self.cfg.carry_lift_lo) / max(_hi - self.cfg.carry_lift_lo, 1e-6)).clamp(0.0, 1.0)
        _down = (1.0 - ((_lift_ref - _hi) / max(_hi, 1e-6)).clamp(0.0, 1.0))
        self.gp_sharpen_seq = (_up * _down) if self.cfg.gp_lift_sharpen else torch.zeros_like(_lift_ref)  # (T,)
        # Binary view for the boolean consumers (ET window, contact-weight precompute, release below).
        self.grasp_window_seq = (self.carry_seq > 0.5).float()
        _grip = self.grasp_window_seq
        # Release phase (2026-06-02, for r_orient): frames AFTER the grip window ends, i.e. the object has
        # been manipulated and placed back down and the hand retreats. r_orient fires here (enclosure has
        # dropped to 0 so the enclosure gate alone would miss the flip). Derived from the grip window's last
        # active frame -> seq-agnostic; on sequences held aloft to the very end (grip window runs to T-1,
        # e.g. seq3) release is EMPTY -> r_orient relies on the enclosure gate only (no retreat flip there).
        _grip_idx = torch.nonzero(_grip > 0.5).flatten()
        _last_grip = int(_grip_idx.max().item()) if _grip_idx.numel() > 0 else _grip.shape[0]
        _ar = torch.arange(_grip.shape[0], device=self.device)
        self.release_seq = (_ar > _last_grip).float()    # (T,) 1 after the grip window ends

        # r_grip_pose CONTACT-PROXIMITY weights (2026-05-31): down-weight keypoints that the HUMAN did NOT
        # wrap onto the object so the plain mean stops diluting the real contact points (the full-20 mean
        # rewarded finger SHAPE without driving the tips into contact -> gp_full/nohaven enclosure ~0).
        # d_center = each kpt's CLOSEST approach to the object center over the grip window; r_obj = the
        # most-wrapped kpt's distance (~surface). w_k = exp(-wbeta*(d_center - r_obj)) in (0,1]: wrapped
        # points ~1, points held off ~0. Computed ONCE from the demo. Data-derived per sequence under ONE
        # identical rule (the wrap-set differs only because the demo differs) -> seq-agnostic. See memory.
        _gw = self.grasp_window_seq > 0.5                                  # (T,) grip-window frames
        _dc_all = torch.norm(self.obj_kpts_pos_seq_offset, dim=-1)         # (T,21) kpt -> obj-center dist
        _dc = _dc_all[_gw].amin(dim=0) if bool(_gw.any()) else _dc_all.amin(dim=0)  # (21,)
        _dc_gk = _dc[self.grip_pose_kpts]                                  # (K,) grip_pose_kpts order
        _r_obj = _dc_gk.min()                                              # ~ surface radius
        _w_raw = torch.exp(-self.cfg.grip_pose_wbeta * (_dc_gk - _r_obj))  # (K,) in (0,1]
        # FLOOR (2026-05-31): keep a minimum weight on EVERY keypoint so non-contact fingers stay pose-
        # constrained (natural hand + well-formed grip), while contact points still dominate. Pure exp
        # (floor=0) left non-contact fingers unconstrained -> sloppy curled/extended fingers in the video.
        self.gp_kpt_weight = self.cfg.grip_pose_wfloor + (1.0 - self.cfg.grip_pose_wfloor) * _w_raw
        # RAW (un-floored) weight: used to decide whether a FINGER is part of the demo's grip (its
        # worst-gate strength). The floor must NOT leak into this -> an unused finger (raw ~0) must be
        # excluded from the four-side worst-gate, else we'd force a finger the human never wrapped
        # (would break seq-agnosticism on sequences that use fewer fingers).
        self.gp_kpt_weight_raw = _w_raw
        # PHASE-DEPENDENT grip weight (phasegrip, 2026-06-04): build a (T,K) weight equal to the static weight
        # on frames where each grip keypoint is at/near its OWN grip-peak, relaxing toward the pose floor on
        # frames where it leaves that peak by > phase_grip_release_dist (a finger the human releases mid-swirl,
        # e.g. seq2 ring/pinky). RELEASE-ONLY: the gate in [0,1] scales only the contact-above-floor part, so it
        # can never demand MORE than the static ratchet -> seq1/seq3 sustained grips are preserved (verified
        # near-noop). Self-relative (each kpt vs its window-min distance _dc_gk) -> seq-agnostic, size-independent.
        # Precomputed for all frames (reference-only, no policy dependence); reward indexes [t] like the targets.
        # phase_grip_weight=False forces the gate to 1 -> gp_kpt_weight_seq[t] == static weight for every t.
        _dcg_seq = _dc_all[:, self.grip_pose_kpts]                                # (T,K) kpt -> obj-center dist
        _gap = (_dcg_seq - _dc_gk.unsqueeze(0)).clamp_min(0.0)                    # (T,K) m past own grip-peak
        _tau = torch.exp(torch.tensor(-self.cfg.grip_pose_wbeta * self.cfg.phase_grip_release_dist,
                                      device=self.device))                        # ratio threshold from release_dist
        _ratio = torch.exp(-self.cfg.grip_pose_wbeta * _gap)                      # (T,K) self-relative engagement (0,1]
        _rel_gate = torch.sigmoid(self.cfg.phase_grip_k * (_ratio - _tau))       # (T,K) ~1 engaged, ~0 released
        if not self.cfg.phase_grip_weight:
            _rel_gate = torch.ones_like(_rel_gate)
        # floored weight per frame: floor + (static contact above floor) * gate  (== static when engaged)
        self.gp_kpt_weight_seq = self.cfg.grip_pose_wfloor + (
            self.gp_kpt_weight - self.cfg.grip_pose_wfloor).unsqueeze(0) * _rel_gate          # (T,K)
        # raw usage per frame: static raw scaled by the same gate (released finger drops out of the usage gate)
        self.gp_kpt_weight_raw_seq = self.gp_kpt_weight_raw.unsqueeze(0) * _rel_gate          # (T,K)

        # Use fingertip contact patches as MANO fingertip keypoints.
        seq_len = self.obj_pos_seq.shape[0]

        self.hand_dof_seq = torch.zeros((seq_len, self.num_hand_dof), device=self.device)
        self.hand_dof_pos_reset[:] = self.hand_dof_seq[0]
        self.hand_rot_reset[:] = self.inputs['R_init'].to(self.device)
        self.hand_pos_reset[:] = (self.inputs['t_init']).to(self.device) + to_center_pos[0]
        # Lift the hand slightly to avoid initial floor contact.
        self.hand_pos_reset[:,2] = self.hand_pos_reset[:,2] + 0.01
    

    def _setup_scene(self):
        # Provided code. Do not modify.

        # add hand, object
        self.hand = Articulation(self.cfg.robot_cfg)
        self.object = RigidObject(self.cfg.object_cfg)
        self.table = RigidObject(self.cfg.table_cfg)

        # add ground plane
        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        # add articulation to scene
        self.scene.articulations["robot"] = self.hand
        self.scene.rigid_objects["object"] = self.object
        self.scene.rigid_objects["table"] = self.table
        
        self.contact_sensors = [
            self.scene.sensors[f"contact_sensor_{body}"]
            for body in self.cfg.fingertip_body_names
        ]

        # add lights
        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
        light_cfg.func("/World/Light", light_cfg)

        # collision group
        stage = omni.usd.get_context().get_stage()
        collisionGroupPaths = [
            "/World/collisionGroup0",
            "/World/collisionGroup1",
            "/World/collisionGroup2",
        ]
        collisionGroupIncludesRel = [None] * 3
        collisionGroupFilteredRels = [None] * 3

        for i in range(3):
            collisionGroup = UsdPhysics.CollisionGroup.Define(stage, collisionGroupPaths[i])
            collisionGroupPrim = collisionGroup.GetPrim()
            collectionAPI = Usd.CollectionAPI.Apply(
                collisionGroupPrim,
                UsdPhysics.Tokens.colliders
            )
            collisionGroupIncludesRel[i] = collectionAPI.CreateIncludesRel()
            collisionGroupFilteredRels[i] = collisionGroup.CreateFilteredGroupsRel()
        
        for i in range(self.num_envs):
            collisionGroupIncludesRel[0].AddTarget(f"/World/envs/env_{i}/Robot")
            collisionGroupIncludesRel[1].AddTarget(f"/World/envs/env_{i}/Object")
            collisionGroupIncludesRel[2].AddTarget(f"/World/envs/env_{i}/table")

        collisionGroupFilteredRels[1].AddTarget(collisionGroupPaths[1])
        collisionGroupFilteredRels[2].AddTarget(collisionGroupPaths[2])


    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        # Provided code. Do not modify.
        self.actions = actions.clone()


    def _apply_action(self) -> None:
        # Provided code. Do not modify.
        pos_offset = self.actions[:, 0:3]
        rot_offset = self.actions[:, 3:9]
        finger_actions = self.actions[:, 9:]
        
        R_offset= rotation_6d_to_matrix(rot_offset)

        # Convert actions into forces and torques
        forces = pos_offset * self.cfg.action_dt * self.cfg.K_pos
        torques = matrix_to_axis_angle(R_offset) * self.cfg.action_dt * self.cfg.K_rot
        forces = (1.0 - self.cfg.global_moving_average) * self.prev_forces + self.cfg.global_moving_average * forces
        torques = (1.0 - self.cfg.global_moving_average) * self.prev_torques + self.cfg.global_moving_average * torques
        with torch.no_grad():
            self.prev_forces = forces.detach().clone()
            self.prev_torques = torques.detach().clone()
        full_forces = torch.zeros((self.num_envs, self.hand.num_bodies, 3), device=self.device)
        full_torques = torch.zeros((self.num_envs, self.hand.num_bodies, 3), device=self.device)

        # Apply forces and torques only on the root(palm)
        full_forces[:, self.root_body[0], :] = forces
        full_torques[:, self.root_body[0], :] = torques
        self.hand.set_external_force_and_torque(
            full_forces,
            full_torques,
            is_global=True,
        )

        
        # Scale DoF and Smooth finger actions
        self.cur_dof_actions[:, self.actuated_dof_indices] = scale(
            finger_actions,
            self.hand_dof_lower_limits[:, self.actuated_dof_indices],
            self.hand_dof_upper_limits[:, self.actuated_dof_indices],
        )
        
        self.cur_dof_actions[:, self.actuated_dof_indices] = (
            self.cfg.act_moving_average * self.cur_dof_actions[:, self.actuated_dof_indices]
            + (1.0 - self.cfg.act_moving_average) * self.prev_dof_actions[:, self.actuated_dof_indices]
        )
        
        self.cur_dof_actions[:, self.actuated_dof_indices] = saturate(
            self.cur_dof_actions[:, self.actuated_dof_indices],
            self.hand_dof_lower_limits[:, self.actuated_dof_indices],
            self.hand_dof_upper_limits[:, self.actuated_dof_indices],
        )
        
        self.prev_dof_actions[:, self.actuated_dof_indices] = self.cur_dof_actions[:, self.actuated_dof_indices]
        # Position control for fingers
        self.hand.set_joint_position_target(
            self.cur_dof_actions[:, self.actuated_dof_indices],
            joint_ids=self.actuated_dof_indices
        )


    def _get_observations(self) -> dict:
        # Provided code. Do not modify.
        obs = self.compute_full_observations()
        observations = {"policy": obs}
        return observations


    def _get_rewards(self) -> torch.Tensor:
        (
            total_reward,
            logs_dict,
        ) = compute_rewards(
            self.hand_kpts_pos,
            self.hand_kpts_target,   # Path B v2: object-relative in grip window (== true MANO elsewhere)
            self.fingertip_pos,
            self.fingertip_pos_ref,
            self.obj_pos,
            self.obj_pos_ref,
            self.obj_rot,
            self.obj_rot_ref,
            self.actions,
            self.hand_dof_vel,
            self.cfg.w_hand,
            self.cfg.w_ft,
            self.cfg.w_op,
            self.cfg.w_or,
            self.cfg.action_penalty_scale * self.reg_mult,   # Path B v6: reg ANNEALED low->high (see reg_mult)
            self.cfg.dof_penalty_scale * self.reg_mult,      #   so fresh exploration discovers grasp at low reg,
            self.cfg.hand_tol,                               #   then the motion is smoothed at high reg.
            self.cfg.ft_tol,
            self.cfg.rot_k,
            self.cfg.or_linear,
            self.cfg.op_z_lin_scale,
        )

        # NOTE: the release-phase hand-RETURN term (r_release_hand) lives DOWN in the _grip_active block
        # below, next to r_release_open, because it is now gated by grip_quality (open-hand gate) which is
        # only defined there. See the "Release-phase decoupling" block after grip_quality.

        # Phase-Aware reward block (v1, 2026-05-29). Replaces the previous monolithic r_grasp.
        # Splits the contact-force reward into r_grasp (PRE-LIFT discovery: credits an opposition
        # pinch while the object is still grounded -> breaks chicken-and-egg) and r_hold (POST-LIFT
        # goal: only fires when ref says airborne AND actual obj is up -> press pathology auto-blocked).
        # Complementary lift_factor gates make the transition smooth and prevent double-counting.
        # pose_gate switched from absolute MANO 21-kpt (which conflicted with r_reach pulling fingers
        # AWAY from MANO toward the grounded object) to object-frame d_obj (consistent with r_reach).
        _grip_active = (self.cfg.w_grasp > 0.0 or self.cfg.w_hold > 0.0
                        or self.cfg.w_reach > 0.0 or self.cfg.w_close > 0.0
                        or self.cfg.ft_grip_suppress > 0.0)
        if _grip_active:
            t = self.t.long()
            # Carry phase gate (verified lift-based, 2026-06-03): smooth carry weight c[t] in [0,1] replaces
            # the previous binary grip window. grip_gate now holds this smooth carry value, so every carry-
            # added term below blends in/out continuously at the approach<->carry<->release edges. Logged as
            # reward/carry for TB so the phase schedule is visible alongside the per-term magnitudes.
            c = self.carry_seq[t]
            grip_gate = c
            logs_dict["reward/carry"] = c

            # --- Shared lift signals (actual obj z) ---
            obj_z_rest = self.obj_pos_seq[0, 2]
            actual_lift = self.obj_pos[:, 2] - obj_z_rest
            actual_lift_factor = torch.sigmoid((actual_lift - 0.5 * self.cfg.lift_gate_margin) * 100.0)
            logs_dict["curriculum/actual_lift"] = actual_lift   # falsifiable signal for the ET-relax test (2026-06-04)

            # CURRICULUM LIFT-GATE accumulator (2026-06-06, [[contact-v2-breaks-seq1-lift]]): accumulate the
            # per-episode lift DEMAND and demand-weighted lift_track so the horizon/anneal `advance` signal
            # can require real lift. demand = UN-DILATED ref-lift ramp (carry_lift_lo..hi): 0 while the ref
            # object is grounded (approach/pre-grip/place), ->1 once the ref is airborne. Using the dilated
            # carry_seq here instead would demand lift during the grounded pre-grip and stall the horizon at
            # frame 0 (observed). lift_track normalizes by each seq's own ref height -> seq-agnostic.
            if self.cfg.horizon_lift_gate and not self.play:
                _ref_lift = self.obj_pos_ref[:, 2] - obj_z_rest
                _lt = (actual_lift / _ref_lift.clamp_min(self.cfg.lift_gate_margin)).clamp(0.0, 1.0)
                _demand = ((_ref_lift - self.cfg.carry_lift_lo) /
                           (self.cfg.carry_lift_hi - self.cfg.carry_lift_lo)).clamp(0.0, 1.0)
                self._ep_demand_sum = self._ep_demand_sum + _demand
                self._ep_lt_wsum = self._ep_lt_wsum + _demand * _lt
                logs_dict["curriculum/ep_lift_adequacy"] = self._ep_lt_wsum / self._ep_demand_sum.clamp_min(1e-6)

            # --- Object-frame fingertip target (shared by r_reach, r_close, pose_gate_obj) ---
            # target = actual obj_pos + R(actual obj_rot) . human_offset_local. The offset rotates
            # with the object through 180-deg flips, so d_obj stays a valid grip-quality signal in
            # rotated configurations (seq2/3). Single computation, reused 3x below.
            off_local = self.obj_fingertip_offset_local[t]                       # (N,F,3)
            q = self.obj_rot.unsqueeze(1).expand(-1, off_local.shape[1], -1).reshape(-1, 4)
            target = self.obj_pos.unsqueeze(1) + quat_apply(q, off_local.reshape(-1, 3)).reshape(off_local.shape)
            d_per = torch.norm(self.fingertip_pos - target, dim=-1)              # (N,F) per-fingertip dist
            d_mean = d_per.mean(dim=-1)
            d_thumb = d_per[:, 0]                                                # thumb = index 0 (th,ff,mf,rf,lf)
            d_four = d_per[:, 1:].mean(dim=-1)                                   # opposing 4-finger group
            # Reach aggregation (2026-05-29). Every HOCAP grip is an OPPOSITION grasp: thumb on one
            # side, the other 4 fingers on the other. With a plain 5-finger MEAN the thumb is only 1/5
            # of r_reach, so the policy satisfies it with the 4 easy fingers and abandons the thumb
            # (pa_v2 grip moment: 4 fingers ~3-5cm to target, thumb ~10cm -> no cage -> object slips).
            # "thumb_split" weights the thumb-side and the 4-finger-side EQUALLY (50/50), mirroring how
            # `enclosure` already models the pinch as thumb x max-opposing-finger -> the reach drive and
            # the contact reward finally share the same opposition topology (their mismatch is why the
            # fingers reached on average but enclosure stayed ~0). seq-agnostic. Toggle reach_aggregation.
            # C2 (2026-05-29, "thumb_split_max"): gate on the WORSE of the two opposition sides,
            # min(g_thumb, g_four) == exp(-k*max(d_thumb,d_four)). The 50/50 SUM ("thumb_split") let
            # the policy collect 0.5 by satisfying ONE side, so it parked at "thumb in / 4 fingers 8cm
            # out" (pa_v3: enclosure stayed 0, horizon stalled at 138). Requiring BOTH sides near
            # forces a simultaneous cage -> the only state where enclosure (thumb x finger force) fires.
            # The 4-finger side still averages internally (smooth); only the two SIDES take the min.
            def _reach_gate(k):
                g_thumb = torch.exp(-k * d_thumb)
                g_four = torch.exp(-k * d_four)
                if self.cfg.reach_aggregation == "thumb_split_max":
                    return torch.minimum(g_thumb, g_four)             # C2: worse side gates (both required)
                if self.cfg.reach_aggregation == "thumb_split":
                    return 0.5 * (g_thumb + g_four)                   # C1: 50/50 sum (one side suffices -> parks)
                if self.cfg.reach_aggregation == "worst":
                    return torch.exp(-k * d_per.amax(dim=-1))
                return torch.exp(-k * d_mean)
            pose_gate_obj = _reach_gate(self.cfg.reach_k)                        # in [0,1]

            # --- Enclosure (continuous opposition pinch + any-contact tail) ---
            # Per-fingertip normal force saturated by tanh -> gradient on ANY contact. Opposition
            # product (thumb x max opposing) requires a true cage. any-contact mean (weight=gcw)
            # supplies first-contact gradient. fingertip_contact_forces_buf[:,0] is (N,5) normal
            # force; thumb is index 0 (fingertip_body_names = th,ff,mf,rf,lf).
            f_sat = torch.tanh(self.fingertip_contact_forces_buf[:, 0] / self.cfg.grasp_force_scale)
            opposition = f_sat[:, 0] * f_sat[:, 1:].amax(dim=-1)
            enclosure = opposition + self.cfg.grasp_contact_w * f_sat.mean(dim=-1)
            self.last_enclosure = enclosure.detach()
            self.last_opposition = opposition.detach()    # SCOOP grip-gate: pinch-vs-scoop discriminator EMA
            logs_dict["reward/enclosure"] = enclosure

            # --- Contact closure: opposition-free force-closure (2026-06-05, seq2 fix) ---
            # See gr_env_cfg use_contact_closure. enclosure(opposition) is ~0 for seq2/seq3 SAME-SIDE scoop
            # grasps so every grip reward built on it was dead there. contact_closure requires the k STRONGEST
            # fingertip contacts to ALL press at once (product of top-k saturated normal forces) -> a real
            # multi-finger grip with NO side/opposition requirement; a 4-finger scoop and a thumb-finger pinch
            # both satisfy it. Real PhysX contact force, so a BATTED/ballistic object (no fingertip contact)
            # scores 0 -- unlike the kinematic comove fallback. grip_contact = max(enclosure, contact_closure):
            # seq1's pinch keeps enclosure (max selects it -> ~unchanged); seq2/seq3 get the revived signal.
            if self.cfg.use_contact_closure:
                topk = f_sat.topk(self.cfg.grip_contact_k, dim=-1).values        # (N,k) strongest contacts
                contact_closure = topk.prod(dim=-1)                              # in [0,1]; needs k simultaneous
                grip_contact_base = torch.maximum(enclosure, contact_closure)
                self.last_contact_closure = contact_closure.detach()             # SCOOP grip-gate scoop-branch EMA
                logs_dict["reward/contact_closure"] = contact_closure
            else:
                grip_contact_base = enclosure
            # Unified live grip signal for carry-manipulation rewards. Today this is the existing max of
            # opposition enclosure and fingertip contact-closure; if seq3 still lifts with near-zero contact,
            # add a stricter support_contact term here instead of creating a separate object-tracking gate.
            grip_quality = grip_contact_base
            logs_dict["reward/grip_quality"] = grip_quality

            # --- Release-phase decoupling: leave the object PLACED, RETURN the hand home (2026-06-10) ---
            # Both terms gated by the hard 0/1 release_seq schedule -> identically 0 across approach+carry (no
            # grasp/lift leak) and identically 0 on seq3 (release window empty) -> seq3 byte-identical.
            #   r_release_open: penalize residual force-grip so the hand opens once the object is placed.
            #   r_release_hand: distance-LINEAR hand-RETURN, gated so it pays ONLY when the object is left at its
            #     reference AND the hand is open. TWO gates:
            #       (1-grip_release): force-grip gate. NOTE it was a NO-OP for the observed failure -- v1==v2
            #         dump (obj dragged 13cm, fingertips 3.5cm from it, hand 16cm from home). The drag is a
            #         LOW-FORCE finger-CLING, so grip_quality(contact force) ~ 0 -> (1-grip) ~ 1 -> no bite.
            #       place_gate = clamp(1 - obj_err/tol): the REAL fix. If the hand drags the object off its
            #         reference, this kills the return reward, so the only way to collect it is to retreat
            #         WITHOUT disturbing the object (clear the fingers). obj_err measures decoupling directly,
            #         independent of contact force. r_op supplies the gradient that pulls the object back to ref.
            #     release_hand_lin_scale=0.30 stays (constant ~3.3/m pull home). seq3 release empty -> still 0.
            _rel = self.release_seq[t]
            grip_release = grip_quality.clamp(0.0, 1.0)
            if self.cfg.release_open_penalty > 0.0:
                r_release_open = self.cfg.release_open_penalty * _rel * grip_release
                total_reward = total_reward - r_release_open
                logs_dict["reward/r_release_open"] = r_release_open
            if self.cfg.release_hand_track:
                _hand_err_rel = torch.mean(torch.norm(self.hand_kpts_pos - self.mano_kpts_pos_ref, dim=-1), dim=-1)
                _obj_err_rel = torch.norm(self.obj_pos - self.obj_pos_ref, dim=-1)
                _place_gate = torch.clamp(1.0 - _obj_err_rel / self.cfg.release_place_tol, 0.0, 1.0)
                r_release_hand = (self.cfg.w_release_hand * _rel * (1.0 - grip_release) * _place_gate
                                  * torch.clamp(1.0 - _hand_err_rel / self.cfg.release_hand_lin_scale, 0.0, 1.0))
                total_reward = total_reward + r_release_hand
                logs_dict["reward/r_release_hand"] = r_release_hand
                logs_dict["reward/release_place_gate"] = _place_gate
                logs_dict["reward/release_gate"] = _rel

            logs_dict["reward/pose_gate_obj"] = pose_gate_obj
            logs_dict["err/reach"] = d_mean               # 5-finger mean dist (continuity w/ prior runs)
            logs_dict["err/reach_thumb"] = d_thumb        # thumb-side dist: does thumb_split pull it in?
            logs_dict["err/reach_four"] = d_four          # 4-finger-side dist

            # --- r_grasp: PRE-LIFT discovery ---
            # Fires in the grip window (incl. 10f before liftoff) while the object is still grounded.
            # gate = grip_gate * (1 - lift_factor) -> reward dies as obj rises -> r_hold takes over.
            # pose_gate_obj instead of absolute-MANO pose_gate: fingertips correctly placed on the
            # grounded actual object are credited, which is exactly what r_reach also pulls toward.
            _r_grip_total = torch.zeros_like(total_reward)
            if self.cfg.w_grasp > 0.0:
                r_grasp = self.cfg.w_grasp * grip_gate * (1.0 - actual_lift_factor) * pose_gate_obj * grip_quality
                total_reward = total_reward + r_grasp
                _r_grip_total = _r_grip_total + r_grasp
                logs_dict["reward/r_grasp"] = r_grasp

            # --- r_hold: POST-LIFT goal (lift-DESATURATED, 2026-05-30) ---
            # Fires only when ref says object should be airborne AND the actual object is up.
            # No pose_gate: a free object can only be held aloft with a physically valid grip.
            # lift_track replaces the old actual_lift_factor (sigmoid*100, saturated at ~5cm so the
            # policy had no reason to lift past 5cm). Use the LINEAR completion ratio actual/ref: its
            # gradient (1/ref_lift) is CONSTANT across the whole lift, so the hard break-off at the
            # start is rewarded as strongly as the final cm (exp(-k*deficit) was weakest exactly at
            # break-off). 0 when grounded (press pathology -> 0), 1 at the per-frame reference height,
            # clamped above (over-lift handled by r_op). Normalizing by each seq's own ref height keeps
            # it seq-agnostic. ref_airborne gates it, so the denom is always >= lift_gate_margin.
            if self.cfg.w_hold > 0.0:
                ref_lift_height = self.obj_pos_ref[:, 2] - obj_z_rest
                lift_track = (actual_lift / ref_lift_height.clamp_min(self.cfg.lift_gate_margin)).clamp(0.0, 1.0)
                # CO-MOVEMENT grip signal (2026-06-04) — topology-agnostic fallback for r_hold's contact gate.
                # WHY: `enclosure` = thumb_tip x opposing-finger_tip force is an OPPOSITION-pinch metric.
                # verify_seq2_enclosure.py proved seq2/seq3 grasps are SAME-SIDE (0% opposition vs 100% for
                # seq1) [[enclosure-structurally-zero-seq2-seq3]] -> enclosure ~ 0 for them even under perfect
                # tracking, so r_hold = w*c*lift_track*enclosure was structurally dead and seq2 never learned a
                # transferable grasp. A free object held ALOFT (lift_track>0) and CO-MOVING with the fingertips
                # is grasped regardless of pinch-vs-scoop-vs-wrap topology, and no fingertip-force/opposition is
                # required. comove = proximity * velocity_lock in [0,1]:
                #   proximity     = object stays near the nearest fingertip (loose 10cm slack so seq2's grip on
                #                   the far END of an elongated object -- 6-8cm from the object origin -- passes;
                #                   only a knocked-away object is suppressed).
                #   velocity_lock = object linear velocity matches the mean fingertip velocity (rigidly carried
                #                   -> ~0 relative; dropped/independent -> diverges -> ~0).
                # The contact gate becomes max(enclosure, comove): for seq1's opposition pinch enclosure already
                # fires so max() selects it (r_hold essentially unchanged -> minimal seq1 impact, by design);
                # for seq2/seq3 enclosure~0 so comove takes over and revives the hold signal. r_hold's lift_track
                # still zeroes it on the ground, so a grounded object earns nothing here even if comove~1 (no
                # pre-lift exploit, anti-press preserved). r_grasp/palm gates keep using raw enclosure unchanged.
                if self.cfg.use_comove_hold:
                    v_ft_mean = self.fingertip_linvel.mean(dim=1)                                  # (N,3)
                    rel_v = torch.norm(self.obj_linvel - v_ft_mean, dim=-1)                         # (N,)
                    d_min = torch.norm(self.fingertip_pos - self.obj_pos.unsqueeze(1), dim=-1).min(dim=1).values
                    proximity = torch.exp(-5.0 * torch.clamp_min(d_min - self.cfg.comove_prox_slack, 0.0))
                    velocity_lock = torch.exp(-self.cfg.comove_vel_k * rel_v)
                    comove = proximity * velocity_lock                                              # (N,) in [0,1]
                    grip_contact = torch.maximum(grip_quality, comove)
                    logs_dict["reward/comove"] = comove
                    logs_dict["reward/grip_contact"] = grip_contact
                else:
                    grip_contact = grip_quality    # = max(enclosure, contact_closure); enclosure if toggle off
                # Gate on the smooth carry weight c (was the binary ref_airborne); lift_track still zeroes the
                # term before liftoff, so pressing the grounded object earns nothing (anti-press preserved).
                r_hold = self.cfg.w_hold * c * lift_track * grip_contact
                total_reward = total_reward + r_hold
                _r_grip_total = _r_grip_total + r_hold
                logs_dict["reward/r_hold"] = r_hold
                logs_dict["err/lift_deficit"] = torch.clamp_min(ref_lift_height - actual_lift, 0.0)

            # Feed combined grip reward to reg-anneal EMA (originally just r_grasp). Because r_grasp
            # now drops to 0 once the policy is reliably lifting (lift_factor -> 1), using r_grasp
            # alone would never re-trigger the reg ramp at the threshold (0.20). Sum captures both
            # the early discovery and steady-state hold signal so the ramp behavior matches v6.
            self.last_r_grasp = _r_grip_total.detach()

            # --- Carry-phase manipulation gate on object position & rotation credit ---
            # seq2 pathology [[seq2-slide-on-table-gaming]]: its ref lifts the object to a TRANSIENT peak then
            # PLACES IT BACK on the table, so the time-averaged r_op_xy / r_or are fully satisfiable by SLIDING
            # the grounded object to the right (x,y) + yaw WITHOUT ever lifting -> the policy parks in a no-grasp
            # slide optimum (enclosure~0, actual_lift~0; confirmed by frame-0 play). r_op_z is z-linear, so if
            # it stays ungated it can still pay a no-grip lift/balance policy. Fix: during the CARRY phase ONLY,
            # gate the full object-position (xy+z), object-rotation, and axis-purity credit by how far the
            # object is ACTUALLY lifted and gripped. carry_gate = (1-c) + c*lift_track*grip_factor:
            #   * outside carry (approach / place-down, c~0) -> 1.0  -> seq1's place-on-table ending + every
            #     approach are untouched (this is why a blanket enclosure-gate was rejected: it would kill the
            #     placement credit).
            #   * inside carry, if the object is lifted to ref height AND grip_quality is firm -> ~1.0 -> no
            #     regression on real grasp/lift trajectories.
            #   * inside carry while the object stays grounded OR lifts without grip -> ~0 -> the free object
            #     tracking credit vanishes, forcing the policy through the grasp+lift it was skipping.
            # ONE identical, seq-agnostic rule (mirrors the existing carry-gates on r_grasp/r_hold/r_grip_pose).
            # Subtracts the slide-collectable fraction of the credit compute_rewards already added to total.
            carry_pos_gate = torch.ones_like(total_reward)
            _ref_lift = (self.obj_pos_ref[:, 2] - obj_z_rest).clamp_min(self.cfg.lift_gate_margin)
            _lift_track = (actual_lift / _ref_lift).clamp(0.0, 1.0)
            if self.cfg.carry_pos_lift_gate:
                # GRIP-GATE EXTENSION (2026-06-07, seq3 balance-lift fix [[seq3-balance-lift-no-grip]]): the
                # lift-only gate blocked seq2's no-lift SLIDE but NOT seq3's lift-WITHOUT-grip BALANCE -- the
                # book RESTS on the hand (contact_closure ~ 0) yet lift_track > 0, so the gate passed and
                # handed out full xy/rot credit. Confirmed by frame-0 play + TB contact_closure_ema flat ~0
                # over 2800 ep while actual_lift reached 20cm. Require a REAL grip too: grip_factor SATURATES
                # to 1.0 once grip_quality (= max(enclosure, contact_closure)) exceeds grip_gate_ref, so
                # it is a NO-OP wherever a firm grip already exists -> seq1 (enclosure 0.77 >> ref=0.12) is
                # byte-neutral, while seq3's balance (cc ~ 0) loses the carry xy/rot credit and is forced into
                # a real grip. THRESHOLD (clamp), not raw multiply, so a legitimately soft scoop grip is not
                # penalized. seq-agnostic (one rule; ref sits in the empty gap between 0=no-grip and
                # 0.68=seq1-grip). Toggle carry_pos_grip_gate=False -> grip_factor==1 -> exact lift-only revert.
                if self.cfg.carry_pos_grip_gate:
                    grip_factor = (grip_quality / self.cfg.grip_gate_ref).clamp(0.0, 1.0)
                else:
                    grip_factor = torch.ones_like(_lift_track)
                carry_pos_gate = (1.0 - c) + c * _lift_track * grip_factor          # (N,) in [0,1]
                total_reward = total_reward + self.cfg.w_op * 0.5 * logs_dict["reward/r_op_xy"] * (carry_pos_gate - 1.0)
                total_reward = total_reward + self.cfg.w_op * 0.5 * logs_dict["reward/r_op_z"] * (carry_pos_gate - 1.0)
                total_reward = total_reward + self.cfg.w_or * logs_dict["reward/r_or"] * (carry_pos_gate - 1.0)
                logs_dict["reward/carry_pos_gate"] = carry_pos_gate
                logs_dict["reward/grip_factor"] = grip_factor

            # Optional lift bootstrap (currently disabled): if training deadlocks because manip_gate never
            # turns on, uncomment this small attempt reward so near-object lift exploration gets a runway.
            # Keep the weight small; full r_op/r_or credit should remain gated by grip_quality above.
            # r_lift_attempt = 0.3 * c * pose_gate_obj * _lift_track
            # total_reward = total_reward + r_lift_attempt
            # logs_dict["reward/r_lift_attempt"] = r_lift_attempt

            # --- r_or_axis: swing-twist rotation-AXIS purity (object-only, grip-safe) 2026-06-08 ---
            # r_or = clamp(1-theta/pi) is total-geodesic = AXIS-AGNOSTIC, so the policy meets the rotation
            # MAGNITUDE on the cheap vertical-YAW axis and still collects r_or (dump: seq2 carry off-axis
            # SWING 52deg at correct 150deg magnitude; seq1 3.9deg). Decompose the ACTUAL rotation-from-frame0
            # into TWIST about the reference axis (precomputed self.ref_rot_axis) + SWING (everything off that
            # axis) and penalize the swing angle, angle-linear like or_linear. Sign-free in a_ref (it appears
            # twice in the projection). Object-only -> never pulls the hand off the object (unlike the
            # palmframe / absolute-MANO graveyard); magnitude-gated by ref_rot_angle so non-rotating phases
            # and seq1's near-pure axis are ~neutral. Flag default OFF = byte-identical; dump pre-validated.
            #
            # ACTUAL-ROTATION COUPLING (2026-06-08, [[release-hand-return-term]] regression fix): the original
            # form rewarded clamp(1-swing/pi), which a STATIONARY object satisfies trivially (no rotation ->
            # swing 0 -> full reward). That paid seq1 a free ~0.39 "park" reward during ref-rotation frames
            # (ax_gate up to 0.75 at 135deg) and so REINFORCED the no-motion equilibrium that broke seq1 after
            # releasehand (which had no axis term). Multiply by actual_frac = clamp(actual_rot/ref_rot): a still
            # object earns 0 (park incentive removed -> seq1-neutral by construction), and the term only pays
            # for on-axis rotation actually achieved -> a STRONGER, correct axis-purity driver for seq2/seq3
            # (which DO rotate). One byte-identical change, improves all 3. See seq2-finger-manipulation.
            if self.cfg.or_axis_align:
                q_ar = quat_mul(self.obj_rot, quat_conjugate(self.obj_rot_reset))   # (N,4) actual rot from frame0
                a_ref = self.ref_rot_axis[t]                                        # (N,3)
                _wv = q_ar[:, 0]; _vv = q_ar[:, 1:]
                _proj = (_vv * a_ref).sum(-1, keepdim=True) * a_ref                 # twist part of the vector
                _tw = torch.cat([_wv.unsqueeze(-1), _proj], dim=-1)
                _tw = _tw / torch.norm(_tw, dim=-1, keepdim=True).clamp_min(1e-8)
                _twinv = torch.cat([_tw[:, :1], -_tw[:, 1:]], dim=-1)
                _sw = quat_mul(q_ar, _twinv)                                        # swing = q * twist^-1
                swing = 2.0 * torch.atan2(torch.norm(_sw[:, 1:], dim=-1), _sw[:, 0].abs())   # (N,) 0..pi
                # actual rotation magnitude from frame 0, as a fraction of the reference -> 0 when the object
                # is still (kills the free-stillness reward), saturates at 1 when it matches the ref magnitude.
                actual_rot_angle = 2.0 * torch.atan2(torch.norm(q_ar[:, 1:], dim=-1), q_ar[:, 0].abs())  # (N,) 0..pi
                actual_frac = (actual_rot_angle / self.ref_rot_angle[t].clamp_min(0.05)).clamp(0.0, 1.0)
                r_or_axis = torch.clamp(1.0 - swing / 3.141592653589793, 0.0, 1.0)
                ax_gate = (self.ref_rot_angle[t] / 3.141592653589793).clamp(0.0, 1.0)        # active where ref rotates
                if self.cfg.or_axis_gate_r_or:
                    # Make axis purity a gate on the already carry-gated r_or credit, not just an additive bonus.
                    # This preserves early rotation gradient through the floor while preventing wrong-axis
                    # rotations from receiving full geodesic-angle reward in seq2/seq3 carry windows.
                    axis_factor = self.cfg.or_axis_gate_floor + (1.0 - self.cfg.or_axis_gate_floor) * r_or_axis
                    axis_gate = c * ax_gate
                    r_or_axis_factor = 1.0 - axis_gate * (1.0 - axis_factor)
                    total_reward = total_reward + (
                        self.cfg.w_or * logs_dict["reward/r_or"] * carry_pos_gate * (r_or_axis_factor - 1.0)
                    )
                    logs_dict["reward/r_or_axis_factor"] = r_or_axis_factor
                r_or_axis_term = self.cfg.w_or_axis * carry_pos_gate * ax_gate * actual_frac * r_or_axis
                total_reward = total_reward + r_or_axis_term
                logs_dict["reward/r_or_axis"] = r_or_axis_term
                logs_dict["err/swing_deg"] = swing * 57.29577951308232

            # --- r_ft suppression in grip window (pa_v5 original: full suppression) ---
            # logs_dict["reward/r_ft"] is the UNWEIGHTED exp tracking term; the previous compute_rewards
            # already added w_ft*r_ft to total. Remove the suppressed fraction and report the kept value.
            # r_ft tracks the MANO (reference) fingertips. REVIVING it inside the grip window (pa_v6/v7,
            # 2026-05-30) deepened the contact-free hand-tracking optimum: enclosure collapsed to 0 and
            # the forward-horizon froze at the lift wall (frame ~139) -- the policy chased the MANO pose
            # instead of making real contact. So suppress r_ft fully across the grip window; r_reach
            # (object-anchored) is the fingertip driver there. Reverted to isolate the lift_track effect.
            if self.cfg.ft_grip_suppress > 0.0 and "reward/r_ft" in logs_dict:
                keep = 1.0 - self.cfg.ft_grip_suppress * grip_gate
                total_reward = total_reward - self.cfg.w_ft * (1.0 - keep) * logs_dict["reward/r_ft"]
                logs_dict["reward/r_ft"] = logs_dict["reward/r_ft"] * keep

            # --- r_reach: object-frame kinematic pull (reuses d_obj) ---
            if self.cfg.w_reach > 0.0:
                r_reach = self.cfg.w_reach * grip_gate * pose_gate_obj   # pose_gate_obj = _reach_gate(reach_k)
                total_reward = total_reward + r_reach
                logs_dict["reward/r_reach"] = r_reach

            # --- r_palm: object-frame hand-ROOT proximity (anti-splay) ---
            # Fingertip-only r_reach can be satisfied by splaying the fingers while the palm stays back
            # (pa_v4: palm 6cm too far, fingers 17 vs 12.7cm spread -> open poking hand, enclosure 0).
            # Pull the hand root to its object-frame target so the palm must come IN; the fingers then
            # close onto the object instead of reaching with extended tips. Object-local target rotates
            # with the actual object -> drift-robust (no MANO-trap, unlike absolute r_ft). See memory.
            if self.cfg.w_palm > 0.0:
                palm_target = self.obj_pos + quat_apply(self.obj_rot, self.obj_palm_offset_local[t])
                d_palm = torch.norm(self.hand_pos - palm_target, dim=-1)
                r_palm = self.cfg.w_palm * grip_gate * torch.exp(-self.cfg.reach_k * d_palm)
                total_reward = total_reward + r_palm
                logs_dict["reward/r_palm"] = r_palm
                logs_dict["err/palm"] = d_palm

            # --- r_palmframe: REFERENCE-anchored palm frame (wrist + MCPs) = the ROTATION driver (2026-05-31) ---
            # The gross hand orientation (palm frame) is what rotates a grasped object, but grip_pose anchors
            # the fingers to the ACTUAL object pose -> satisfiable WITHOUT rotating (gp_cw_v1: tips 3cm yet
            # wrist 9cm / palm 47deg off -> object under-rotated). Track wrist + 5 MCPs to the object at the
            # REFERENCE rotation (actual position + reference orientation): matching it forces the palm to
            # adopt the rotated pose, which rotates the held object (distal/grip_pose keeps the fingers on the
            # real object -> no grab-air). During approach/grasp ref==actual so this also pins the palm
            # (subsumes r_palm's anti-splay, hence w_palm default 0); the anchors diverge only once rotation
            # is demanded -> a DENSE "where the wrist should go" signal (better gradient than r_or's outcome-
            # only reward). Uniform weight (palm kpts are NOT contact points -> contact-weighting would wrongly
            # down-weight them). Reference-anchored from each seq's own demo -> seq-agnostic.
            if self.cfg.w_palmframe > 0.0:
                pk = self.palmframe_kpts
                offp = self.obj_kpt_offset_local[t][:, pk]                                  # (N,P,3) object-local
                qkr = self.obj_rot_ref.unsqueeze(1).expand(-1, offp.shape[1], -1).reshape(-1, 4)
                tgtp = self.obj_pos.unsqueeze(1) + quat_apply(qkr, offp.reshape(-1, 3)).reshape(offp.shape)
                d_pf = torch.norm(self.hand_kpts_pos[:, pk] - tgtp, dim=-1).mean(dim=-1)     # (N,)
                # GATE ON ACTUAL ENCLOSURE (anchor_v3, 2026-06-01): the palmframe target uses the REFERENCE
                # rotation, so during the airborne window it sits 10-18cm OFF the actual (un-rotated) object.
                # Firing it before a grip exists pulls the hand off the object -> contact never forms
                # (anchor_v1/v2: enclosure flat 0, hand parked in the contact-free reference-tracking haven,
                # r_hand 0.93 / r_grasp 0). Multiply by the actual enclosure (clamped to 1) so palmframe is
                # SILENT until the object is genuinely held, then ramps in to rotate the HELD object -- the
                # same complementary-gate logic r_hold uses (x enclosure). Solves the chicken-and-egg: grip
                # forms first (pfm behavior), rotation pressure only once there is a grip to transmit torque.
                # Hyperparameter-free, seq-agnostic (enclosure is data-driven contact).
                palm_enc_gate = enclosure.clamp(0.0, 1.0)
                r_palmframe = self.cfg.w_palmframe * grip_gate * palm_enc_gate * torch.exp(-self.cfg.grip_pose_k * d_pf)
                total_reward = total_reward + r_palmframe
                logs_dict["reward/r_palmframe"] = r_palmframe
                logs_dict["err/palmframe"] = d_pf

            # --- r_close: flexion drive gated by proximity to obj-frame target ---
            if self.cfg.w_close > 0.0:
                act = self.actuated_dof_indices
                span = (self.hand_dof_upper_limits[:, act] - self.hand_dof_lower_limits[:, act]).clamp_min(1e-6)
                flex = ((self.hand_dof_pos[:, act] - self.hand_dof_lower_limits[:, act]) / span).mean(dim=-1)
                near = _reach_gate(self.cfg.close_gate_k)   # same thumb/4-finger split, closure sharpness
                r_close = self.cfg.w_close * grip_gate * near * flex
                total_reward = total_reward + r_close
                logs_dict["reward/r_close"] = r_close
                logs_dict["close/flex"] = flex

            # --- r_grip_pose: object-anchored FULL-finger grip configuration (candidate, 2026-05-30) ---
            # Anchor the human grip POSE (all finger keypoints) to the ACTUAL object and reward matching it.
            # Unlike r_reach (5 fingertip positions, under-determines the 18-DOF hand), this specifies the
            # full finger curl on the real object -> directly addresses the verified under-specification that
            # froze pa_v8/v9 at a partial pinch. Phantom-free (object-anchored). err/grip_pose: low+enclosure
            # rising = reference is reachable AND a valid grip; low but enclosure~0 = pose ok but no contact
            # (penetration/IK needed); high = pose unreachable (retarget needed).
            if self.cfg.w_grip_pose > 0.0:
                gk = self.grip_pose_kpts
                off = self.obj_kpt_offset_local[t][:, gk]                              # (N,K,3)
                qk = self.obj_rot.unsqueeze(1).expand(-1, off.shape[1], -1).reshape(-1, 4)
                tgt = self.obj_pos.unsqueeze(1) + quat_apply(qk, off.reshape(-1, 3)).reshape(off.shape)
                d_per = torch.norm(self.hand_kpts_pos[:, gk] - tgt, dim=-1)             # (N,K) per-keypoint
                # Opposition-aware aggregation (thumb vs other-4): gate on the WORSE side so the THUMB must
                # match, otherwise the plain mean under-weights it and the opposition cage never forms.
                # CONTACT-PROXIMITY WEIGHTED mean (2026-05-31): within each side, weight each keypoint by
                # gp_kpt_weight so the points the human WRAPPED on the object dominate and palm-side MCPs /
                # non-grip fingers (which diluted the tips and let the full-20 pose match without contact)
                # are ~0. The data-derived weights make this seq-agnostic (see precompute / cfg.grip_pose_wbeta).
                # Thumb side: contact-weighted mean (one finger).
                gpw_t = self.gp_kpt_weight_seq[t]                                       # (N,K) phase-dependent per-env (== static rows if disabled)
                # LIFT-ONSET SHARPEN (2026-06-05): raise the exp sharpness during the reference break-off band
                # so a LOOSE grip's credit collapses and the lagging scoop finger is pulled onto the object.
                # k_eff = grip_pose_k*(1+gain*s[t]); s=0 off the band -> k_eff == grip_pose_k (no-op elsewhere).
                _gp_k = self.cfg.grip_pose_k * (1.0 + self.cfg.gp_sharpen_gain * self.gp_sharpen_seq[t])
                _wt = gpw_t[:, self.gp_thumb_mask]                                       # (N,Kt)
                d_thumb = (d_per[:, self.gp_thumb_mask] * _wt).sum(dim=-1) / _wt.sum(dim=-1).clamp_min(1e-6)
                g_thumb = torch.exp(-_gp_k * d_thumb)
                # Four side: PER-FINGER MEAN, usage-weighted (2026-05-31). Each finger's contact-weighted
                # mean distance -> gate g_f; aggregate by the MEAN over the fingers the demo uses (raw
                # weight as usage). Unlike the old 16-keypoint POOLED mean (where the index tip was ~1/16
                # and masked by palm-side joints -> averaged away -> thumb-side pinch), each FINGER is
                # ~1/4 here, giving a lagging finger (e.g. index) ~4x the pull. Unlike min/product (which
                # equalize distances and kill the grasp -- wg_v1 enclosure~0), the mean keeps the
                # commit-incentive that bootstraps contact. POSITION-ONLY: enclosure untouched. No new knob.
                _gu, _d_f, _u = [], [], []
                for fm in self.gp_finger_masks:
                    _wf = gpw_t[:, fm]                                                  # (N,Kf) floored: pose-shaping
                    d_f = (d_per[:, fm] * _wf).sum(dim=-1) / _wf.sum(dim=-1).clamp_min(1e-6)
                    g_f = torch.exp(-_gp_k * d_f)
                    use_f = self.gp_kpt_weight_raw_seq[t][:, fm].amax(dim=-1)           # (N,) raw: finger usage this frame
                    _gu.append(g_f * use_f)
                    _d_f.append(d_f)
                    _u.append(use_f)
                _usum = torch.stack(_u, dim=0).sum(dim=0).clamp_min(1e-6)               # (N,) per-env usage total
                g_four = torch.stack(_gu, dim=0).sum(dim=0) / _usum                     # usage-weighted finger mean
                d_four = torch.stack(_d_f, dim=0).amax(dim=0)                           # worst-finger dist (logging)
                # r_grip_pose = object-anchored full-finger grip configuration (carry_v3, ungated). The v4
                # object-tracking gate and v5 phase-aware lift gate were both REVERTED (2026-06-04): carry_v3
                # was the known-good config (user confirmed grip quality from the mid-training play video);
                # the v4/v5 gates on top of it regressed the grasp. seq3 lift is to be addressed without
                # touching this term.
                r_grip_pose = self.cfg.w_grip_pose * grip_gate * torch.minimum(g_thumb, g_four)
                total_reward = total_reward + r_grip_pose
                logs_dict["reward/r_grip_pose"] = r_grip_pose
                logs_dict["err/grip_pose"] = (d_per * gpw_t).sum(dim=-1) / gpw_t.sum(dim=-1).clamp_min(1e-6)
                logs_dict["err/grip_pose_thumb"] = d_thumb
                logs_dict["err/grip_pose_four"] = d_four   # now = WORST used finger's weighted-mean dist

            # --- r_orient: hand-orientation tracking, gated to grip+release (2026-06-02) -------------
            # Wrist ROLL is a near-null-space direction of the position rewards (a full palm flip moves the
            # 21 keypoints only ~3cm when the hand is flat), so r_hand/r_ft can neither stop the retreat
            # palm-UP flip orlin's vigorous lift+pour excites NOR finely drive the pour orientation.
            # r_orient tracks the MANO-reference palm FRAME directly (angle-LINEAR, like or_linear: constant
            # gradient, no flat 180deg antipode -> can drag a flipped palm all the way back). Default GATE keeps
            # the validated enclosure+release behavior. An optional grip_quality carry gate is available for
            # seq2/3 topology experiments, but left off by default so this axis-gate patch stays isolated.
            if self.cfg.w_orient > 0.0:
                def _palm_frame(K):                    # K:(N,21,3) -> (N,3,3) cols [x,y,z]
                    o = K[:, 0]
                    x = K[:, 9] - o                    # wrist -> middle MCP (forward)
                    x = x / (x.norm(dim=-1, keepdim=True) + 1e-8)
                    v = K[:, 17] - o                   # wrist -> pinky MCP (in-plane)
                    z = torch.cross(x, v, dim=-1)      # palm normal
                    z = z / (z.norm(dim=-1, keepdim=True) + 1e-8)
                    y = torch.cross(z, x, dim=-1)
                    return torch.stack([x, y, z], dim=-1)
                R_rel = _palm_frame(self.hand_kpts_pos).transpose(-1, -2) @ _palm_frame(self.mano_kpts_pos_ref)
                cos = ((R_rel[:, 0, 0] + R_rel[:, 1, 1] + R_rel[:, 2, 2]) - 1.0) * 0.5
                theta = torch.acos(torch.clamp(cos, -1.0, 1.0))                       # (N,) geodesic 0..pi
                if self.cfg.orient_use_grip_quality_gate:
                    carry_orient_gate = c * _lift_track * (grip_quality / self.cfg.grip_gate_ref).clamp(0.0, 1.0)
                    orient_gate = torch.maximum(carry_orient_gate, self.release_seq[t])
                else:
                    orient_gate = torch.maximum(enclosure.clamp(0.0, 1.0), self.release_seq[t])
                r_orient = self.cfg.w_orient * orient_gate * torch.clamp(1.0 - theta / 3.141592653589793, 0.0, 1.0)
                total_reward = total_reward + r_orient
                logs_dict["reward/r_orient"] = r_orient
                logs_dict["reward/orient_gate"] = orient_gate
                logs_dict["err/orient"] = theta * (180.0 / 3.141592653589793)        # deg, for TB

            logs_dict["reward/total"] = total_reward

        for key, value in logs_dict.items():
            if key not in self.logs_dict:
                self.logs_dict[key] = value.detach()
            else:
                self.logs_dict[key] += value.detach()

        if "log" not in self.extras:
            self.extras["log"] = dict()

        return total_reward


    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        self._compute_intermediate_values()

        # Time out at the per-env step cap OR when the reference trajectory reaches its end.
        # With the forward-horizon curriculum the cap is the (growing) horizon during training,
        # so episodes are short early and lengthen as the policy masters the current frontier;
        # during play the full episode is rolled out.
        if not self.play:
            cap = min(int(self.horizon), self.max_episode_length - 1)
        else:
            cap = self.max_episode_length - 1
        self.time_out = (self.episode_length_buf >= cap) | (self.t >= self.seq_len - 1)

        early_terminate = self.early_terminate if self.termination else torch.zeros_like(self.early_terminate, device=self.device)
        return early_terminate, self.time_out


    def _reset_idx(self, env_ids: Sequence[int] | None):
        if env_ids is None:
            env_ids = self.hand._ALL_INDICES
        # Forward-horizon curriculum: grow the episode horizon from how the just-ended episode went.
        # Done before super() because the survival signal is read from the pre-reset state.
        self._update_horizon_curriculum(env_ids)
        # resets articulation and rigid body attributes
        super()._reset_idx(env_ids)
        # Reset object
        self._reset_object(env_ids)
        # Reset hand
        self._reset_hand(env_ids)

        for key, value in self.logs_dict.items():
            self.extras["log"][key] = value.mean()
        self.logs_dict = dict()
        
        self.successes[env_ids] = 0
        # Step the object-friction scaffold (high early -> annealed to nominal). Training-only; writes to
        # all envs only when the scheduled friction has moved (cheap). Side-effect free during play.
        self._apply_friction_anneal()
        # Step the object-MASS scaffold (light early -> annealed to nominal) the same way. Training-only.
        self._apply_mass_anneal()
        # Path B v6 regularization anneal (training-only): once the grasp is ESTABLISHED, ratchet the
        # smoothness reg from its low exploration value up to full to smooth the final motion.
        if not self.play:
            self.grasp_ema = (self.cfg.reg_anneal_ema * self.grasp_ema
                              + (1.0 - self.cfg.reg_anneal_ema) * float(self.last_r_grasp.mean()))
            if self.grasp_ema > self.cfg.reg_anneal_grasp_thresh and self.reg_mult < 1.0:
                self.reg_mult = min(1.0, self.reg_mult + self.cfg.reg_anneal_step)
            # 2026-05-28: enclosure EMA on the same scheme as grasp_ema, used by the friction-anneal gate.
            self.enclosure_ema = (self.cfg.reg_anneal_ema * self.enclosure_ema
                                  + (1.0 - self.cfg.reg_anneal_ema) * float(self.last_enclosure.mean()))
            # SCOOP grip-gate EMAs (same scheme): opposition_ema (pinch-vs-scoop discriminator) +
            # contact_closure_ema (opposition-free grip signal for the scoop branch of _grip_learned).
            self.opposition_ema = (self.cfg.reg_anneal_ema * self.opposition_ema
                                   + (1.0 - self.cfg.reg_anneal_ema) * float(self.last_opposition.mean()))
            self.contact_closure_ema = (self.cfg.reg_anneal_ema * self.contact_closure_ema
                                        + (1.0 - self.cfg.reg_anneal_ema) * float(self.last_contact_closure.mean()))
            self.extras.setdefault("log", dict())
            self.extras["log"]["curriculum/reg_mult"] = torch.as_tensor(self.reg_mult, device=self.device)
            self.extras["log"]["curriculum/grasp_ema"] = torch.as_tensor(self.grasp_ema, device=self.device)
            self.extras["log"]["curriculum/enclosure_ema"] = torch.as_tensor(self.enclosure_ema, device=self.device)
            self.extras["log"]["curriculum/opposition_ema"] = torch.as_tensor(self.opposition_ema, device=self.device)
            self.extras["log"]["curriculum/contact_closure_ema"] = torch.as_tensor(self.contact_closure_ema, device=self.device)
        self._compute_intermediate_values()


    def _apply_friction_anneal(self):
        # Push the current object friction (self.obj_friction) to the sim when it changed, and log it.
        # The VALUE is decided in _update_horizon_curriculum: it starts
        # at obj_friction_high and is ratcheted toward nominal ONLY on batches where the policy completes
        # the (near-)full trajectory without ET at the current friction -> the hold length and anneal rate
        # auto-adapt per sequence with one identical rule, and friction never races ahead of the policy
        # (no rug-pull). Training-only; play never touches the material, so it keeps the nominal friction.
        # NOTE: env state isn't checkpointed, so a resumed run restarts at obj_friction_high (benign: it
        # re-eases then re-ratchets as the horizon recovers; same limitation self.horizon already has).
        if not self.cfg.use_friction_anneal or self.play:
            return
        mu = float(self.obj_friction)
        self.extras.setdefault("log", dict())
        self.extras["log"]["curriculum/obj_friction"] = torch.as_tensor(mu, device=self.device)
        if self._friction_applied is not None and abs(mu - self._friction_applied) < 1e-6:
            return
        mats = self.object.root_physx_view.get_material_properties()  # (num_inst, num_shapes, 3), on CPU
        mats[:, :, 0] = mu   # static friction
        mats[:, :, 1] = mu   # dynamic friction
        self.object.root_physx_view.set_material_properties(mats, torch.arange(mats.shape[0], device="cpu"))
        self._friction_applied = mu


    def _apply_mass_anneal(self):
        # Push the current object mass (obj_mass_frac * nominal) to the sim when the fraction changed, and
        # log it. The FRACTION is decided in _update_horizon_curriculum on the same progress gate as
        # friction: it starts at obj_mass_low_frac and is ratcheted toward 1.0 ONLY on batches where the
        # policy completes the (near-)full trajectory without ET at the current mass -> never races ahead.
        # The nominal mass is captured lazily here on the first call (before any override) so we scale each
        # sequence's own USD mass. Training-only; play never touches it, keeping the nominal USD mass.
        # NOTE: env state isn't checkpointed, so a resumed run restarts at obj_mass_low_frac (benign: it
        # re-eases then re-ratchets as the horizon recovers; same limitation self.horizon/friction have).
        if not self.cfg.use_mass_anneal or self.play:
            return
        if self.obj_mass_nominal is None:
            # (num_inst, 1) on CPU; the true USD mass, read once before we ever override it.
            self.obj_mass_nominal = self.object.root_physx_view.get_masses().clone()
        self.extras.setdefault("log", dict())
        self.extras["log"]["curriculum/obj_mass_frac"] = torch.as_tensor(float(self.obj_mass_frac), device=self.device)
        if self._mass_applied is not None and abs(self.obj_mass_frac - self._mass_applied) < 1e-6:
            return
        target = self.obj_mass_frac * self.obj_mass_nominal
        self.object.root_physx_view.set_masses(target, torch.arange(target.shape[0], device="cpu"))
        self._mass_applied = self.obj_mass_frac


    def _set_object_state(self, pos, rot, env_ids, vel=None):
        default_states = self.object.data.default_root_state[env_ids].clone()
        default_states[:, :3] = pos + self.scene.env_origins[env_ids]
        default_states[:, 3:7] = rot

        if vel is not None:
            default_states[:, 7:13] = vel
        
        self.object.write_root_state_to_sim(default_states, env_ids=env_ids)

        self.obj_pos[env_ids] = self.obj_pos_reset[env_ids]
        self.obj_rot[env_ids] = self.obj_rot_reset[env_ids]


    def _reset_object(self, env_ids):
        # RSI: place the object at its reference pose for each env's sampled start frame
        # (frame 0 when RSI is off / during play), and seed it with the reference velocity
        # so a mid-trajectory reset is dynamically continuous.
        k = self.start_frame_idx[env_ids].long()
        self.obj_pos_reset[env_ids] = self.obj_pos_seq[k]
        self.obj_rot_reset[env_ids] = self.obj_rot_seq[k]
        vel = torch.cat((self.obj_linvel_seq[k], self.obj_angvel_seq[k]), dim=-1)
        self._set_object_state(self.obj_pos_reset[env_ids], self.obj_rot_reset[env_ids], env_ids, vel=vel)


    def _set_hand_state(self, pos, rot, dof_pos, dof_vel, root_vel, dof_target, ext_force, ext_torque, env_ids):
        hand_default_state = self.hand.data.default_root_state.clone()
        hand_default_state[env_ids, 0:3] = pos + self.scene.env_origins[env_ids]
        hand_default_state[env_ids, 3:7] = rot
        hand_default_state[env_ids, 7:13] = root_vel

        self.hand.write_root_pose_to_sim(hand_default_state[env_ids, :7], env_ids=env_ids)
        self.hand.write_root_velocity_to_sim(hand_default_state[env_ids, 7:13], env_ids=env_ids)
        self.hand.write_joint_state_to_sim(dof_pos, dof_vel, env_ids=env_ids)
        self.hand.set_joint_position_target(dof_target[:, self.actuated_dof_indices], self.actuated_dof_indices, env_ids=env_ids)
        self.hand.set_external_force_and_torque(ext_force, ext_torque, env_ids=env_ids, is_global=self.is_global)

        self.prev_dof_actions[env_ids] = dof_target.clone()
        self.cur_dof_actions[env_ids] = dof_target.clone()
        self.prev_forces[env_ids] = ext_force[:, self.root_body[0], :].clone()
        self.prev_torques[env_ids] = ext_torque[:, self.root_body[0], :].clone()
        
        self.hand_pos[env_ids] = self.hand_pos_reset[env_ids]
        self.hand_rot[env_ids] = self.hand_rot_reset[env_ids]


    def _reset_hand(self, env_ids):
        # Forward-horizon always resets at frame 0, so the hand starts at its frame-0 reference pose
        # (hand_pos_reset / hand_rot_reset) with the fingers open. The policy must discover the
        # approach->grasp->lift->place motion itself; the friction bootstrap supplies the early
        # grip gradient (see _update_horizon_curriculum).
        dof_pos = self.hand_dof_pos_reset[env_ids].clone()

        dof_vel = torch.zeros_like(self.hand.data.default_joint_vel[env_ids])
        root_vel = torch.zeros_like(self.hand.data.default_root_state[env_ids, 7:13])

        hand_global_force = torch.zeros((len(env_ids), self.hand.num_bodies, 3), device=self.device)
        hand_global_torque = torch.zeros((len(env_ids), self.hand.num_bodies, 3), device=self.device)

        self._set_hand_state(self.hand_pos_reset[env_ids], self.hand_rot_reset[env_ids], dof_pos, dof_vel, root_vel, dof_pos, hand_global_force, hand_global_torque, env_ids)


    def _is_scoop(self):
        # Topology test shared by the mass/friction curriculum gate and the lift-gate bootstrap decouple:
        # real opposition-free multi-finger contact (contact_closure_ema) WITH opposition ABSENT => a
        # same-side scoop (seq2/seq3), not a (weak) pinch. PROVABLY seq1-NEUTRAL: seq1's pinch keeps the
        # thumb in the top-2 contacts so opposition_ema == contact_closure_ema -> opposition is never
        # < opp_scoop_frac*contact_closure -> always False for seq1.
        if not self.cfg.use_scoop_grip_gate:
            return False
        return (self.contact_closure_ema > self.cfg.mass_grip_contact_thresh
                and self.opposition_ema < self.cfg.opp_scoop_frac * self.contact_closure_ema)

    def _grip_learned(self, ema_thresh):
        # "Is a real grip forming" for the mass/friction curriculum gate, topology-aware.
        #   pinch branch (seq1): opposition-based enclosure_ema crosses ema_thresh -- the original rule.
        #   scoop branch (seq2/seq3): enclosure is ~0 (no opposition) so instead require a genuine scoop
        #     (_is_scoop). PROVABLY seq1-NEUTRAL: seq1's pinch keeps the scoop branch False so this returns
        #     exactly the pinch branch (enclosure_ema > ema_thresh).
        return (self.enclosure_ema > ema_thresh) or self._is_scoop()

    def _update_horizon_curriculum(self, env_ids):
        # Forward-horizon curriculum: every episode starts at frame 0 (the only physically valid
        # reset, since fingers reset open and a mid-lift reset would drop the object) -- this is
        # also the play/eval condition. During play the full trajectory is rolled out; there is no
        # curriculum to advance.
        self.start_frame_idx[env_ids] = 0
        if self.play or len(env_ids) == 0:
            return

        # Grow the horizon one-sided when enough finishing envs reached the current horizon without
        # early termination. Because it never shrinks and concentrates samples at the frontier, it
        # parks at the lift onset until grasp+lift is learned, then advances.
        cap = min(int(self.horizon), self.max_episode_length - 1)
        reached = self.episode_length_buf[env_ids] >= cap
        # CURRICULUM LIFT-GATE (2026-06-06, [[contact-v2-breaks-seq1-lift]]): an env counts as advanced
        # only if, over the frames where the ref demanded lift, the demand-weighted mean lift_track cleared
        # the threshold. Kills the no-lift "reach the cap on the table" exploit that opened seq1's horizon to
        # full with lift=0. An episode that demanded no lift yet (approach-only horizon, demand_sum~0) passes
        # freely so the horizon can still advance through the on-table approach.
        #
        # MASS-BOOTSTRAP DECOUPLE (2026-06-07, [[curriculum-lift-gate-fix]] regression on seq3): this gate
        # deadlocked the scoop mass-ratchet. For a same-side scoop (seq2/seq3) the FULL-mass object is not
        # liftable until the policy has bootstrapped lift on the light crutch, but the gate refuses to advance
        # the horizon until lift_track>=thresh -> horizon parks at the lift onset -> mass_anneal_horizon_frac
        # never met -> mass trapped at the low crutch -> lift never transfers to nominal (play: 0/510 airborne;
        # massanneal_v1 hit 20cm BEFORE this gate existed). FIX: while a SCOOP is still on the light-mass
        # crutch (mass ramping), advance the horizon freely exactly as massanneal_v1 did -> seq3 learns lift
        # light, horizon opens, mass ratchets, and by the time mass reaches nominal the lift is already learned.
        # Gated on _is_scoop so seq1's PINCH keeps the lift-gate during its own ramp (its no-lift exploit is
        # still blocked); and re-enforced for scoops once mass is nominal (catches seq2's on-table slide at
        # full mass). Seq-agnostic: keyed only on the shared mass curriculum + topology discriminator.
        mass_ramping = self.cfg.use_mass_anneal and self.obj_mass_frac < (self.cfg.obj_mass_nominal_frac - 1e-3)
        # SEQ2 DEADLOCK FIX (2026-06-08, [[seq2-horizon-deadlock]]): bypass the lift-gate during the light-mass
        # bootstrap for ALL topologies, not just confirmed scoops. _is_scoop needs contact_closure_ema > thresh,
        # but seq2's contact never forms (chicken-egg: needs the horizon past the grasp frames to form contact,
        # needs contact to be recognized as a scoop to advance the horizon) -> horizon froze at the carry onset
        # (69) for 1500 ep. The lift-gate is only needed at NOMINAL mass (where seq1's no-lift exploit lives);
        # during the light crutch every topology can lift, so a blanket bypass restores massanneal_v1's working
        # behavior and gives seq2 the runway to reach + learn the grasp. Re-enforced once mass is nominal.
        # Bypass keyed on the REFERENCE topology (_ref_is_scoop, precomputed from demo geometry -> known
        # before contact) instead of the blanket lift_gate_bootstrap_all (which disabled the gate for seq1's
        # pinch and reopened its no-lift exploit). seq1=pinch -> bypass OFF -> lift-gate enforced through the
        # ramp; seq2/seq3=scoop -> bypass ON pre-contact -> runway to form the grasp. lift_gate_bootstrap_all
        # (now default False) stays as an explicit override; live _is_scoop() kept as a redundant safety.
        mass_bootstrap = mass_ramping and (
            self.cfg.lift_gate_bootstrap_all or self._ref_is_scoop or self._is_scoop())
        if self.cfg.horizon_lift_gate and not mass_bootstrap:
            _ds = self._ep_demand_sum[env_ids]
            _adq = self._ep_lt_wsum[env_ids] / _ds.clamp_min(1e-6)
            lift_ok = (_ds < 1e-6) | (_adq >= self.cfg.horizon_lift_thresh)
        else:
            lift_ok = torch.ones_like(reached)
        advance = (reached & (~self.early_terminate[env_ids]) & lift_ok).float().mean()
        if advance > self.cfg.horizon_advance_thresh:
            # Adaptive step: grow faster the more comfortably the frontier was cleared, so easy
            # phases (on-table approach) advance quickly while hard phases (grasp/lift/place)
            # self-throttle (advance drops near the threshold -> step shrinks toward horizon_step).
            margin = (advance - self.cfg.horizon_advance_thresh) / max(
                1e-6, 1.0 - self.cfg.horizon_advance_thresh)
            step = self.cfg.horizon_step * (1.0 + self.cfg.horizon_accel * float(margin))
            self.horizon = min(self.horizon + step, float(self.max_episode_length - 1))

        # Friction-anneal gate REDESIGN (2026-05-28): primary gate is enclosure_ema (real contact
        # evidence; not horizon-completion which is gameable by hand-only tracking). Safety net: if
        # the gate hasn't fired for friction_force_step_every reset batches, force one step anyway so
        # friction still reaches nominal before training ends (eval/grading runs at nominal). Patch A
        # (lift_gate = ref*actual in r_grasp) handles the pressing pathology in the reward itself, so
        # the friction gate only needs to detect "is real contact happening" via enclosure_ema.
        if self.cfg.use_friction_anneal and self.obj_friction > self.cfg.obj_friction_nominal:
            horizon_done = self.horizon >= self.cfg.friction_anneal_horizon_frac * (self.max_episode_length - 1)
            advance_ok = float(advance) > self.cfg.friction_advance_thresh
            grip_learned = self._grip_learned(self.cfg.friction_grip_ema_thresh)   # SCOOP gate (same bug as mass)
            gate_fired = horizon_done and advance_ok and grip_learned
            self._friction_idle_batches += 1
            force_step = self._friction_idle_batches >= self.cfg.friction_force_step_every
            if gate_fired or force_step:
                self.obj_friction = max(self.obj_friction - self.cfg.friction_step,
                                        float(self.cfg.obj_friction_nominal))
                self._friction_idle_batches = 0
            self.extras.setdefault("log", dict())
            self.extras["log"]["curriculum/friction_idle"] = torch.as_tensor(
                self._friction_idle_batches, device=self.device)

        # Object-MASS ratchet (SCOOP bootstrap, 2026-06-04): mirrors the friction gate but raises mass
        # LOW->nominal (friction lowers high->nominal). Same signals: only ramp once the horizon has
        # mastered the trajectory under the light crutch (horizon_done), the policy still clears the
        # frontier (advance_ok), and a real grip exists (enclosure_ema) -> mass never races ahead. Safety
        # force-step so mass reaches nominal even on a stuck run (grading runs at nominal mass).
        if self.cfg.use_mass_anneal and self.obj_mass_frac < self.cfg.obj_mass_nominal_frac:
            horizon_done = self.horizon >= self.cfg.mass_anneal_horizon_frac * (self.max_episode_length - 1)
            advance_ok = float(advance) > self.cfg.mass_advance_thresh
            grip_learned = self._grip_learned(self.cfg.mass_grip_ema_thresh)   # SCOOP gate: enclosure OR scoop-contact
            gate_fired = horizon_done and advance_ok and grip_learned
            self._mass_idle_batches += 1
            force_step = self._mass_idle_batches >= self.cfg.mass_force_step_every
            if gate_fired or force_step:
                self.obj_mass_frac = min(self.obj_mass_frac + self.cfg.mass_step_frac,
                                         float(self.cfg.obj_mass_nominal_frac))
                self._mass_idle_batches = 0
            self.extras.setdefault("log", dict())
            self.extras["log"]["curriculum/mass_idle"] = torch.as_tensor(
                self._mass_idle_batches, device=self.device)
        self.extras.setdefault("log", dict())
        self.extras["log"]["curriculum/horizon"] = torch.as_tensor(self.horizon, device=self.device)
        self.extras["log"]["curriculum/horizon_reached_rate"] = advance.detach()
        # CURRICULUM LIFT-GATE (2026-06-06): log the per-batch pass rate, then reset the accumulators for the
        # envs that just ended so the next episode starts fresh at 0. Reset MUST come after `advance` /
        # `lift_ok` above have consumed the just-ended values.
        if self.cfg.horizon_lift_gate:
            self.extras["log"]["curriculum/lift_gate_pass_rate"] = lift_ok.float().mean().detach()
            self._ep_demand_sum[env_ids] = 0.0
            self._ep_lt_wsum[env_ids] = 0.0


    def _collect_target(self):
        # RSI: the reference frame each env tracks is its sampled start plus the number of
        # steps elapsed since reset, clamped to the last frame of the trajectory.
        t = torch.clamp(self.start_frame_idx.long() + self.episode_length_buf, max=self.seq_len - 1)
        self.t = t
        t_next = torch.clamp(t + 1, max=self.seq_len - 1)
        
        # current ref
        self.obj_pos_ref = self.obj_pos_seq[t]
        self.obj_rot_ref = self.obj_rot_seq[t]
        self.obj_linvel_ref = self.obj_linvel_seq[t]
        self.obj_angvel_ref = self.obj_angvel_seq[t]
        self.obj_linvel_value_ref = self.obj_linvel_value_seq[t]
        self.obj_angvel_value_ref = self.obj_angvel_value_seq[t]

        self.fingertip_pos_ref = self.fingertip_pos_seq[t]
        self.mano_kpts_pos_ref = self.mano_kpts_pos_seq[t]
        
        # next ref
        self.obj_pos_next = self.obj_pos_seq[t_next]
        self.obj_rot_next = self.obj_rot_seq[t_next]
        self.obj_linvel_next = self.obj_linvel_seq[t_next]
        self.obj_angvel_next = self.obj_angvel_seq[t_next]
        self.obj_linvel_value_next = self.obj_linvel_value_seq[t_next]
        self.obj_angvel_value_next = self.obj_angvel_value_seq[t_next]

        self.hand_dof_next = self.hand_dof_seq[t_next]
        self.fingertip_pos_next = self.fingertip_pos_seq[t_next]
        self.mano_kpts_pos_next = self.mano_kpts_pos_seq[t_next]


    def _collect_state(self):
        # data for object
        object_state = self.object.data.root_state_w
        self.obj_pos = object_state[:,:3] - self.scene.env_origins
        self.obj_rot = object_state[:,3:7]
        self.obj_linvel = object_state[:,7:10]
        self.obj_angvel = object_state[:,10:13]

        # data for hand
        hand_state = self.hand.data.root_state_w
        self.hand_pos = hand_state[:, :3] - self.scene.env_origins
        self.hand_rot = hand_state[:, 3:7]
        self.hand_linvel = hand_state[:,7:10]
        self.hand_angvel = hand_state[:,10:13]
        self.hand_dof_pos = self.hand.data.joint_pos
        self.hand_dof_vel = self.hand.data.joint_vel

        # data for handbodies
        body_state = self.hand.data.body_state_w[:, self.hand_bodies]
        hand_bodies_pos = body_state[:, :, :3]
        self.hand_bodies_pos = hand_bodies_pos - self.scene.env_origins.unsqueeze(1)
        self.hand_bodies_rot = body_state[:, :, 3:7]
        self.hand_bodies_linvel = body_state[:, :, 7:10]
        self.hand_bodies_angvel = body_state[:, :, 10:13]

        # data for fingertips
        fingertip_pos = self.hand_bodies_pos[:, self.fingertip_bodies]
        self.fingertip_rot = self.hand_bodies_rot[:, self.fingertip_bodies]
        self.fingertip_linvel = self.hand_bodies_linvel[:, self.fingertip_bodies]
        self.fingertip_angvel = self.hand_bodies_angvel[:, self.fingertip_bodies]

        # NaN/inf guard (2026-05-28, seq2 ep146 crash fix): PhysX can return non-finite pose/vel when a
        # policy in mid-training applies extreme actions on the longer/higher-rotation seq2/3 trajectories
        # (seq1 v6 trained 6900ep without hitting this). A single NaN here propagates through quat_to_6d
        # -> obs -> policy net -> sigma_logits NaN -> torch.normal() crashes with "std >= 0.0". Sanitize
        # at the choke point so EVERY downstream consumer (obs, reward, ET) sees finite values. Out-of-
        # place nan_to_num: most of the raw assignments above are VIEWS into physics buffers, so we must
        # NOT mutate them in-place (would corrupt sim state) -- reassign as fresh clones. Same code on
        # all 3 seqs -> identical-config rule preserved (this is a numerical guard, not a hyperparam).
        def _clean(_t):
            return torch.nan_to_num(_t, nan=0.0, posinf=0.0, neginf=0.0)
        def _clean_quat(_q):
            _q = torch.nan_to_num(_q, nan=0.0, posinf=0.0, neginf=0.0)
            _n = _q.norm(dim=-1, keepdim=True)
            _bad = _n < 1e-6
            _q = torch.where(_bad, torch.zeros_like(_q), _q)
            _w = torch.where(_bad.squeeze(-1), torch.ones_like(_q[..., 0]), _q[..., 0])
            _q = torch.cat((_w.unsqueeze(-1), _q[..., 1:]), dim=-1)
            return _q / _q.norm(dim=-1, keepdim=True).clamp_min(1e-6)
        # obj_pos / hand_pos / hand_bodies_pos are subtraction results (already fresh tensors) so in-place
        # would be safe, but reassigning is uniform and cheap.
        self.obj_pos = _clean(self.obj_pos)
        self.obj_rot = _clean_quat(self.obj_rot)
        self.obj_linvel = _clean(self.obj_linvel)
        self.obj_angvel = _clean(self.obj_angvel)
        self.hand_pos = _clean(self.hand_pos)
        self.hand_rot = _clean_quat(self.hand_rot)
        self.hand_linvel = _clean(self.hand_linvel)
        self.hand_angvel = _clean(self.hand_angvel)
        self.hand_dof_pos = _clean(self.hand_dof_pos)
        self.hand_dof_vel = _clean(self.hand_dof_vel)
        self.hand_bodies_pos = _clean(self.hand_bodies_pos)
        self.hand_bodies_rot = _clean_quat(self.hand_bodies_rot)
        self.hand_bodies_linvel = _clean(self.hand_bodies_linvel)
        self.hand_bodies_angvel = _clean(self.hand_bodies_angvel)
        fingertip_pos = _clean(fingertip_pos)
        self.fingertip_rot = _clean_quat(self.fingertip_rot)
        self.fingertip_linvel = _clean(self.fingertip_linvel)
        self.fingertip_angvel = _clean(self.fingertip_angvel)

        # normal, axis
        self.normal = quat_apply(self.fingertip_rot, self.fingertip_normal)
        offset = quat_apply(self.fingertip_rot, self.fingertip_offset)
        # Use fingertip contact patches as MANO fingertip keypoints.
        self.hand_kpts_pos[:, self.cfg.MANO_kpts_except_fingertips] = self.hand_bodies_pos[:, self.cfg.body_to_kpts_except_fingertips]
        self.hand_kpts_pos[:, self.cfg.MANO_fingertips] = fingertip_pos + offset

        self.fingertip_pos = self.hand_kpts_pos[:, self.cfg.MANO_fingertips]
        
        # data for fingertip sensors
        for i in range(self.num_fingertips):
            force = self.contact_sensors[i].data.force_matrix_w
            self.fingertip_contact_forces[:, i] = force[:, 0, 0]
        self.fingertip_contact_forces_buf[:, 0] = torch.clamp_min((self.fingertip_contact_forces * (-self.normal)).sum(dim=-1), 0)



    def _compute_intermediate_values(self):
        self._collect_target()
        self._collect_state()

        # Path B v6 (2026-05-28): rolled back Path B v2's object-relative target. v2 was added to
        # cure a pre-grasp 6cm hand-object gap, but it REMOVED the implicit lift incentive baked
        # into r_hand: when the target is anchored to the ACTUAL (grounded) object, hovering near
        # the object already saturates r_hand (~0.95) and contact buys nothing. v8 TB confirmed
        # this: r_hand=0.948, r_grasp=0.000, enclosure=0.000 for 3900ep -- the policy parked at
        # the ungrippable local optimum because lifting cost effort but earned no reward.
        # v6 SOLVED with the absolute target (ep~2500 grasp jump), so pre-grasp pull-to-object
        # is now supplied by r_reach (object-anchored fingertip exp, line ~496) + r_close (flex
        # gated on proximity, line ~511), and r_hand keeps lift pressure on by always pointing
        # at the lifted MANO reference.
        self.hand_kpts_target = self.mano_kpts_pos_ref

        # Early-termination signals (training only). End the episode when the hand or the
        # object drifts too far from the reference, after a grace period so the approximate
        # RSI hand placement has time to settle. Because per-step reward is clamped >= 0,
        # ending early reduces the return, so ET acts as a survival incentive and removes the
        # constant "free" object reward a do-nothing policy used to collect for the full episode.
        if self.termination and self.cfg.use_et:
            hand_err = torch.mean(torch.norm(self.hand_kpts_pos - self.hand_kpts_target, dim=-1), dim=-1)
            # Object-position error with VERTICAL-LIFT-LAG FORGIVENESS (2026-06-04). The flat obj_pos_err
            # wall (0.15m) is exactly the seq3 horizon lock: the ref lift crosses 15cm at frame 118, so a
            # policy that already has the firm grip (enclosure 0.95) but hasn't yet LEARNED the lift gets
            # ET'd the instant the ref lifts -> no survival runway to learn even a 1cm lift -> horizon frozen
            # at 119. seq1 never hits this (its 13cm lift < 15cm). Forgive the object for lagging BELOW its
            # reference lift by up to et_lift_lag_frac of the reference lift height, so the policy survives the
            # early lift frames and can learn the lift (r_hand pulls the hand up; the firm grip carries the
            # object). Horizontal error and OVER-shoot stay FULLY tight -> seq1's manipulation pressure is
            # unchanged and a SOLVED policy (lifts to match ref -> ~0 lag) is unaffected: seq1-inert by
            # construction. The REWARD (r_op/r_hold) still demands the full lift; only the kill is relaxed.
            # seq-agnostic (scales with each seq's own ref lift). FALSIFIABLE: if horizon opens but actual
            # lift stays ~0 -> capability problem, not runway -> revisit with denser lift shaping.
            ref_lift_h = torch.clamp_min(self.obj_pos_ref[:, 2] - self.obj_pos_seq[0, 2], 0.0)
            v_lag_allowed = self.cfg.et_lift_lag_frac * ref_lift_h
            dz = self.obj_pos_ref[:, 2] - self.obj_pos[:, 2]                       # >0 when object lags BELOW ref
            dz_eff = torch.where(dz > 0, torch.clamp_min(dz - v_lag_allowed, 0.0), dz)   # forgive downward lag only
            err_xy = self.obj_pos[:, :2] - self.obj_pos_ref[:, :2]
            obj_pos_err = torch.sqrt((err_xy * err_xy).sum(dim=-1) + dz_eff * dz_eff)
            grace = self.episode_length_buf >= self.cfg.et_grace_steps
            self.hand_far_apart = hand_err > self.cfg.et_hand_thresh
            # Path B (2026-05-27): relax the object-position ET INSIDE the grip window so the policy can
            # CLOSE on the object (and perturb the free body) while learning the grasp, instead of being
            # instantly killed. This unblocks the prior failure where the fingers parked ~2cm out and
            # never closed -- closing ejected the object -> obj_pos_err > thresh -> ET -> death, so the
            # policy learned "approach but don't close". The grip window is the sequence-agnostic airborne
            # window (grasp_window_seq); outside it the strict threshold still terminates a diverged or
            # do-nothing rollout, so the survival incentive is preserved where it matters.
            grip = self.grasp_window_seq[self.t.long()]                                    # (N,) in {0,1}
            et_obj_thresh = torch.where(grip > 0.5, self.cfg.et_obj_pos_thresh_grip, self.cfg.et_obj_pos_thresh)
            self.obj_far_apart = obj_pos_err > et_obj_thresh
            self.early_terminate = (self.hand_far_apart | self.obj_far_apart) & grace
        else:
            self.early_terminate = torch.zeros_like(self.early_terminate)

        if not self.play:
            # Point visualization for debugging; you may change which points are shown.
            debug_vis1 = self.mano_kpts_pos_ref[:, self.cfg.MANO_fingertips] + self.scene.env_origins.unsqueeze(1)
            self.goal_markers.visualize(debug_vis1.view(-1,3))
            debug_vis2 = self.hand_kpts_pos[:, self.cfg.MANO_fingertips] + self.scene.env_origins.unsqueeze(1)
            self.debug_markers.visualize(debug_vis2.view(-1,3))
        else:
            # Play-only per-frame trajectory dump (env 0) for offline error analysis vs the reference.
            # Side-effect free for training (guarded by self.play). Overwrites a fixed npz each step so
            # the file is complete even if the rollout ends early. Disabled unless GR_PLAY_DUMP is set.
            import os as _os
            _dump = _os.environ.get("GR_PLAY_DUMP", "")
            if _dump:
                if not hasattr(self, "_play_dump"):
                    self._play_dump = {k: [] for k in
                                       ("obj_pos", "obj_pos_ref", "obj_rot", "obj_rot_ref",
                                        "hand_kpts", "hand_kpts_ref", "actions", "dof_vel")}
                d = self._play_dump
                d["obj_pos"].append(self.obj_pos[0].detach().cpu().numpy().copy())
                d["obj_pos_ref"].append(self.obj_pos_ref[0].detach().cpu().numpy().copy())
                d["obj_rot"].append(self.obj_rot[0].detach().cpu().numpy().copy())
                d["obj_rot_ref"].append(self.obj_rot_ref[0].detach().cpu().numpy().copy())
                d["hand_kpts"].append(self.hand_kpts_pos[0].detach().cpu().numpy().copy())
                d["hand_kpts_ref"].append(self.mano_kpts_pos_ref[0].detach().cpu().numpy().copy())
                d["actions"].append(self.actions[0].detach().cpu().numpy().copy())
                d["dof_vel"].append(self.hand_dof_vel[0].detach().cpu().numpy().copy())
                import numpy as _np
                _np.savez(_dump, **{k: _np.asarray(v) for k, v in d.items()})


    def compute_full_observations(self):
        # Reference trajectory is time-indexed: the policy needs phase (t/T) and the
        # target-as-error to know where/when to move. 117 state dims + 73 task dims.
        phase = (self.t.float() / float(self.max_episode_length - 1)).unsqueeze(-1)
        obs = torch.cat(
            (
                self.hand_kpts_pos.reshape(self.num_envs, -1),    # 63 : current 21 keypoints xyz
                self.hand_dof_pos[:, self.actuated_dof_indices],  # 18 : actuated finger joints
                self.obj_pos,                                     #  3 : current object position
                quat_to_6d(self.obj_rot),                         #  6 : current object rotation (6D)
                self.actions,                                     # 27 : last policy action
                phase,                                            #  1 : trajectory progress t/T
                (self.mano_kpts_pos_ref - self.hand_kpts_pos).reshape(self.num_envs, -1),  # 63 : keypoint error to target
                self.obj_pos_ref - self.obj_pos,                  #  3 : object position error to target
                quat_to_6d(self.obj_rot_ref),                     #  6 : target object rotation (6D)
                # --- dynamics/rotation augmentation (18) ---
                quat_to_6d(quat_mul(self.obj_rot_ref, quat_conjugate(self.obj_rot))),  # 6 : explicit object rotation ERROR (relative rot), mirroring obj_pos_err
                self.obj_linvel * self.cfg.vel_obs_scale,         #  3 : current object linear velocity
                self.obj_angvel * self.cfg.vel_obs_scale,         #  3 : current object angular velocity
                self.obj_linvel_ref * self.cfg.vel_obs_scale,     #  3 : reference object linear velocity
                self.obj_angvel_ref * self.cfg.vel_obs_scale,     #  3 : reference object angular velocity
            ),
            dim=-1,
        )
        # Final NaN/inf scrub + clamp (2026-05-28, defense in depth alongside _collect_state guard).
        # Guarantees the policy never receives non-finite inputs even if a future obs term skips the
        # collect-state path (e.g. quat math on _ref tensors). Clamp keeps reasonable scale; valid obs
        # are all within +/-50 by design (positions in meters, 6D rot in [-1,1], scaled velocities <1).
        return torch.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0).clamp(-50.0, 50.0)
    

@torch.jit.script
def scale(x, lower, upper):
    return 0.5 * (x + 1.0) * (upper - lower) + lower


@torch.jit.script
def unscale(x, lower, upper):
    return (2.0 * x - upper - lower) / (upper - lower)


@torch.jit.script
def compute_rewards(
    hand_kpts_pos: torch.Tensor,
    mano_kpts_pos_ref: torch.Tensor,
    fingertip_pos: torch.Tensor,
    fingertip_pos_ref: torch.Tensor,
    obj_pos: torch.Tensor,
    obj_pos_ref: torch.Tensor,
    obj_rot: torch.Tensor,
    obj_rot_ref: torch.Tensor,
    actions: torch.Tensor,
    dof_vel: torch.Tensor,
    w_hand: float,
    w_ft: float,
    w_op: float,
    w_or: float,
    action_penalty_scale: float,
    dof_penalty_scale: float,
    hand_tol: float,
    ft_tol: float,
    rot_k: float,
    or_linear: bool = True,
    op_z_lin_scale: float = 0.30,
):
    # Tracking errors (per-env scalars). Raw errors are returned/logged as-is; the tolerance band
    # below is applied ONLY inside the reward so the TB err/* curves still report true tracking.
    hand_err = torch.mean(torch.norm(hand_kpts_pos - mano_kpts_pos_ref, dim=-1), dim=-1)
    ft_err = torch.mean(torch.norm(fingertip_pos - fingertip_pos_ref, dim=-1), dim=-1)
    obj_pos_err = torch.norm(obj_pos - obj_pos_ref, dim=-1)        # true 3D err (logged as err/obj_pos)
    obj_err_xy = torch.norm((obj_pos - obj_pos_ref)[:, :2], dim=-1)
    obj_err_z = torch.abs(obj_pos[:, 2] - obj_pos_ref[:, 2])
    # quaternion geodesic proxy: 0 when aligned, 1 when opposite (sign-invariant). Logged as err/obj_rot.
    obj_rot_err = 1.0 - torch.abs(torch.sum(obj_rot * obj_rot_ref, dim=-1))
    # Geodesic angle (rad, 0..pi) between current and reference orientation, for the reward shaping below.
    obj_rot_angle = 2.0 * torch.acos(torch.clamp(1.0 - obj_rot_err, 0.0, 1.0))

    # Exponential tracking rewards, each in [0, 1]. Coefficients are scaled so the
    # reward stays responsive at the error magnitudes we care about (~cm position,
    # ~tens-of-degrees rotation) instead of saturating near 1.0 and killing the gradient.
    # Hand/fingertip use a tolerance band (full reward within tol) so their easy, near-saturated
    # gradient doesn't crowd out the harder object terms (see hand_tol/ft_tol in cfg).
    hand_err_eff = torch.clamp_min(hand_err - hand_tol, 0.0)
    ft_err_eff = torch.clamp_min(ft_err - ft_tol, 0.0)
    r_hand = torch.exp(-10.0 * hand_err_eff * hand_err_eff)
    r_ft = torch.exp(-50.0 * ft_err_eff * ft_err_eff)
    # Patch B (2026-05-28): distance-linear shape. exp(-120*err^2) is quadratic-sharp: at 17cm err it is
    # 0.03, at 30cm essentially 0 -> no gradient when far -> the policy gets NO signal to lift once it
    # has missed the grip (seq3 ep_8000 plateau). Linear-in-distance: 5cm->0.61, 10cm->0.37, 20cm->0.14,
    # 30cm->0.05 — monotone gradient across the full error range (mirrors the r_or reshape that made
    # 180deg rotation learnable). Precision near zero is fine: ft_tol=0 + r_ft (w=1.0) drive sub-cm.
    # r_op split into a HORIZONTAL (xy) and a VERTICAL (z) part (2026-06-04, "z-linear lift fix").
    # The old r_op = exp(-10*||3D err||) has a FLAT TAIL exactly in the deep-lift region: seq3 lifts
    # 27cm, so a grounded object sits at err~0.27 -> exp(-2.7)=0.067 with gradient ~1.7/m, i.e. almost
    # no pull upward. This is the SAME flat-tail pathology that or_linear already fixed for rotation,
    # but r_op was never linearized -> seq3's lift was unlearnable (etlift_v1: horizon opened to 437,
    # grip firm enclosure 0.90, yet actual_lift ~0). seq1 (13cm lift) barely enters the flat region so
    # the bug stayed hidden there. FIX: keep the sharp exp on the XY error (precise horizontal tracking,
    # seq1 unchanged) but give the VERTICAL deficit a CONSTANT-gradient angle-linear shape
    # clamp(1 - |dz|/scale, 0, 1) -> gradient w_op/(2*scale) ~= 4/m, constant all the way out to the
    # 27cm peak, so the policy feels a steady up-pull to lift instead of a vanishing one. scale=0.30m
    # >= every seq's peak lift so the z term never bottoms out. Averaged (not summed) with the xy term
    # to keep r_op in [0,1] -> w_op weight semantics and the "no single term dominates" balance hold.
    # seq-agnostic (z error is in meters, same for all 3); over-shoot penalized symmetrically via abs.
    r_op_xy = torch.exp(-10.0 * obj_err_xy)
    r_op_z = torch.clamp(1.0 - obj_err_z / op_z_lin_scale, 0.0, 1.0)
    r_op = 0.5 * (r_op_xy + r_op_z)
    # Path B v5 (2026-05-27): r_or reshaped from exp(-40*err^2) [FLAT ZERO above ~90deg -> no gradient to
    # START the large tilt; seq1 needs 135deg, seq2/3 180deg] to a DENSE exp over the geodesic ANGLE:
    # exp(-rot_k*theta). With rot_k~1.0 it is monotone with gradient across the full 0..180deg range
    # (180->0.04, 135->0.09, 90->0.21, 45->0.46), so the policy gets a signal to rotate from any start.
    # or_linear (2026-06-01): angle-LINEAR shape r_or = clamp(1 - theta/pi, 0, 1). CONSTANT gradient
    # (w_or/pi) across the full 0..pi range. exp(-rot_k*theta) is ~flat at large theta (exp(-2.2)=0.10 at
    # 126deg), so it gives NO pull to drag the orientation out of the wrong-axis vertical-YAW local optimum
    # that dump analysis found (act-axis 50-70deg off the reference pour axis; geodesic stuck ~126-130deg).
    # The linear shape keeps a usable gradient at 135deg (3.4x exp) / 180deg (7x) -> the lever onto the
    # correct pour axis. Same [0,1] range -> w_or ceiling unchanged. Gate-free base term -> no catch-22.
    if or_linear:
        r_or = torch.clamp(1.0 - obj_rot_angle / 3.141592653589793, 0.0, 1.0)
    else:
        r_or = torch.exp(-rot_k * obj_rot_angle)

    # Regularization (scales are negative in cfg) to suppress hand-base drift / jitter
    action_penalty = action_penalty_scale * torch.sum(actions * actions, dim=-1)
    dof_penalty = dof_penalty_scale * torch.sum(dof_vel * dof_vel, dim=-1)

    reward = w_hand * r_hand + w_ft * r_ft + w_op * r_op + w_or * r_or
    reward = reward + action_penalty + dof_penalty
    reward = torch.clamp_min(reward, 0.0)

    logs_dict = {
        "reward/total": reward,
        "reward/r_hand": r_hand,
        "reward/r_ft": r_ft,
        "reward/r_op": r_op,
        "reward/r_op_xy": r_op_xy,    # horizontal (exp) part
        "reward/r_op_z": r_op_z,      # vertical lift (constant-gradient) part -> watch this climb on seq3
        "reward/r_or": r_or,
        "reward/action_penalty": action_penalty,
        "reward/dof_penalty": dof_penalty,
        "err/hand": hand_err,
        "err/ft": ft_err,
        "err/obj_pos": obj_pos_err,
        "err/obj_rot": obj_rot_err,
    }

    return reward, logs_dict



# Utils
def quat_to_6d(quat: torch.Tensor) -> torch.Tensor:
    return matrix_to_rotation_6d(matrix_from_quat(F.normalize(quat, dim=-1)))


def rotation_6d_to_matrix(rot_6d: torch.Tensor) -> torch.Tensor:
    a1 = rot_6d[..., 0:3]
    a2 = rot_6d[..., 3:6]
    b1 = F.normalize(a1, dim=-1)
    b2 = a2 - (b1 * a2).sum(dim=-1, keepdim=True) * b1
    b2 = F.normalize(b2, dim=-1)
    b3 = torch.cross(b1, b2, dim=-1)
    return torch.stack((b1, b2, b3), dim=-2)


def matrix_to_rotation_6d(matrix: torch.Tensor) -> torch.Tensor:
    return matrix[..., :2, :].clone().reshape(*matrix.shape[:-2], 6)


def matrix_to_axis_angle(matrix: torch.Tensor) -> torch.Tensor:
    return axis_angle_from_quat(quat_from_matrix(matrix))
