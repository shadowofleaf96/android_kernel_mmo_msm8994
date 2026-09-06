#!/usr/bin/env python3
"""Allow CPP ENQUEUE/APPEND with num_buffs==0.

Bullhead mm-camera calls VIDIOC_MSM_CPP_ENQUEUE_STREAM_BUFF_INFO at
STREAMON to create the identity queue. Native ION buffers are APPENDed
later, so num_buffs is often 0. msm_cpp_subdev_ioctl treated that as
-EINVAL, which aborts ISP streamon (black preview, Camera2 -38).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

P = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/pproc/cpp/msm_cpp.c"
t = P.read_text()

old = """		rc = msm_cpp_copy_from_ioctl_ptr(u_stream_buff_info,
			ioctl_ptr);
		if (rc) {
			ERR_COPY_FROM_USER();
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}
		if (u_stream_buff_info->num_buffs == 0) {
			pr_err("%s:%d: Invalid number of buffers\\n", __func__,
				__LINE__);
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}
		k_stream_buff_info.num_buffs = u_stream_buff_info->num_buffs;
		k_stream_buff_info.identity = u_stream_buff_info->identity;

		if (k_stream_buff_info.num_buffs > MSM_CAMERA_MAX_STREAM_BUF) {
			pr_err("%s:%d: unexpected large num buff requested\\n",
				__func__, __LINE__);
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}

		k_stream_buff_info.buffer_info =
			kzalloc(k_stream_buff_info.num_buffs *
			sizeof(struct msm_cpp_buffer_info_t), GFP_KERNEL);
		if (ZERO_OR_NULL_PTR(k_stream_buff_info.buffer_info)) {
			pr_err("%s:%d: malloc error\\n", __func__, __LINE__);
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}

		rc = (copy_from_user(k_stream_buff_info.buffer_info,
				(void __user *)u_stream_buff_info->buffer_info,
				k_stream_buff_info.num_buffs *
				sizeof(struct msm_cpp_buffer_info_t)) ?
				-EFAULT : 0);
		if (rc) {
			ERR_COPY_FROM_USER();
			kfree(k_stream_buff_info.buffer_info);
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}
"""

new = """		rc = msm_cpp_copy_from_ioctl_ptr(u_stream_buff_info,
			ioctl_ptr);
		if (rc) {
			ERR_COPY_FROM_USER();
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}
		/*
		 * Bullhead mm-camera ENQUEUEs at STREAMON to create the
		 * identity queue. Native ION buffers are APPENDed later,
		 * so num_buffs may be 0. kzalloc(0) is ZERO_SIZE_PTR.
		 */
		pr_err("talkman_cpp STREAM_BUFF cmd=0x%x id=0x%x n=%u ptr=%pK len=%zu\\n",
			cmd, u_stream_buff_info->identity,
			u_stream_buff_info->num_buffs,
			u_stream_buff_info->buffer_info, ioctl_ptr->len);
		k_stream_buff_info.num_buffs = u_stream_buff_info->num_buffs;
		k_stream_buff_info.identity = u_stream_buff_info->identity;
		k_stream_buff_info.buffer_info = NULL;

		if (k_stream_buff_info.num_buffs > MSM_CAMERA_MAX_STREAM_BUF) {
			pr_err("%s:%d: unexpected large num buff requested\\n",
				__func__, __LINE__);
			kfree(u_stream_buff_info);
			mutex_unlock(&cpp_dev->mutex);
			return -EINVAL;
		}

		if (k_stream_buff_info.num_buffs > 0) {
			k_stream_buff_info.buffer_info =
				kzalloc(k_stream_buff_info.num_buffs *
				sizeof(struct msm_cpp_buffer_info_t),
				GFP_KERNEL);
			if (ZERO_OR_NULL_PTR(k_stream_buff_info.buffer_info)) {
				pr_err("%s:%d: malloc error\\n", __func__,
					__LINE__);
				kfree(u_stream_buff_info);
				mutex_unlock(&cpp_dev->mutex);
				return -EINVAL;
			}

			rc = (copy_from_user(k_stream_buff_info.buffer_info,
					(void __user *)u_stream_buff_info->
						buffer_info,
					k_stream_buff_info.num_buffs *
					sizeof(struct msm_cpp_buffer_info_t)) ?
					-EFAULT : 0);
			if (rc) {
				ERR_COPY_FROM_USER();
				kfree(k_stream_buff_info.buffer_info);
				kfree(u_stream_buff_info);
				mutex_unlock(&cpp_dev->mutex);
				return -EINVAL;
			}
		}
"""

if "talkman_cpp STREAM_BUFF" in t:
    print("native STREAM_BUFF patch already present")
elif old not in t:
    raise SystemExit("native STREAM_BUFF pattern not found")
else:
    t = t.replace(old, new, 1)
    print("patched native STREAM_BUFF 0-buffer path")

old2 = """		if (copy_from_user(&k32_cpp_buff_info,
			(void __user *)kp_ioctl.ioctl_ptr,
			sizeof(k32_cpp_buff_info))) {
			pr_err("error: cannot copy user pointer\\n");
			return -EFAULT;
		}

		memset(&k64_cpp_buff_info, 0, sizeof(k64_cpp_buff_info));
		k64_cpp_buff_info.identity = k32_cpp_buff_info.identity;
		k64_cpp_buff_info.num_buffs = k32_cpp_buff_info.num_buffs;
"""

new2 = """		if (copy_from_user(&k32_cpp_buff_info,
			(void __user *)kp_ioctl.ioctl_ptr,
			sizeof(k32_cpp_buff_info))) {
			pr_err("error: cannot copy user pointer\\n");
			return -EFAULT;
		}

		pr_err("talkman_cpp compat STREAM_BUFF k32 id=0x%x n=%u ptr=0x%x ulen=%u\\n",
			k32_cpp_buff_info.identity, k32_cpp_buff_info.num_buffs,
			k32_cpp_buff_info.buffer_info, up32_ioctl.len);

		memset(&k64_cpp_buff_info, 0, sizeof(k64_cpp_buff_info));
		k64_cpp_buff_info.identity = k32_cpp_buff_info.identity;
		k64_cpp_buff_info.num_buffs = k32_cpp_buff_info.num_buffs;
"""

if "talkman_cpp compat STREAM_BUFF" in t:
    print("compat STREAM_BUFF log already present")
elif old2 not in t:
    raise SystemExit("compat STREAM_BUFF pattern not found")
else:
    t = t.replace(old2, new2, 1)
    print("added compat STREAM_BUFF log")

P.write_text(t)
print("apply-cpp-zero-buff done")
