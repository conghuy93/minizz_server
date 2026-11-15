<template>
  <!-- [custom minizjp] Thêm tác nhân = nhập mã 6 số robot đọc ra; tạo agent tên tạm rồi gắn thiết bị.
       Tên agent và Gemini key người dùng tự điền sau trong "Cấu hình vai trò". -->
  <CustomDialog
    :title="$t('addAgentDialog.title')"
    :visible.sync="visible"
    width="420px"
    @confirm="confirm"
    @cancel="cancel"
    @close="handleClose"
    :confirmText="loading ? 'Đang thêm…' : $t('addAgentDialog.confirm')"
    :cancelText="$t('addAgentDialog.cancel')"
    @open="handleOpen"
  >
    <div class="add-agent-body">
      <div class="add-agent-label">
        <span class="required">*</span>
        Mã thiết bị (6 số robot đọc khi khởi động)
      </div>
      <el-input
        maxLength="6"
        ref="inputRef"
        placeholder="Ví dụ: 123456"
        v-model="deviceCode"
        class="add-agent-input code-input"
        inputmode="numeric"
        :disabled="loading"
        @input="deviceCode = deviceCode.replace(/\D/g, '')"
        @keyup.enter.native="confirm"
      />
      <div class="add-agent-hint">
        Bật robot, robot sẽ đọc một mã 6 số. Nhập mã đó vào đây để thêm robot vào tài khoản của bạn.
        Tên tác nhân và Gemini API key có thể đổi sau trong mục "Cấu hình vai trò".
      </div>
    </div>
  </CustomDialog>
</template>

<script>
import Api from '@/apis/api';
import CustomDialog from './CustomDialog.vue';

export default {
  name: 'AddWisdomBodyDialog',
  components: { CustomDialog },
  props: {
    visible: { type: Boolean, required: true }
  },
  data() {
    return {
      deviceCode: "",
      loading: false
    }
  },
  methods: {
    handleOpen() {
      this.$nextTick(() => {
        if (this.$refs.inputRef && this.$refs.inputRef.focus) {
          this.$refs.inputRef.focus();
        }
      });
    },
    confirm() {
      if (this.loading) return;
      const code = (this.deviceCode || "").trim();
      if (!/^\d{6}$/.test(code)) {
        this.$message.error('Vui lòng nhập đúng mã 6 số robot đọc ra');
        return;
      }
      this.loading = true;
      // 1) tạo agent với tên tạm (dùng cấu hình mẫu mặc định: Gemini + VieNeu + PhoWhisper)
      Api.agent.addAgent(`Robot ${code}`, (res) => {
        const body = (res && res.data) || {};
        const agentId = body.data;
        if (body.code !== 0 || !agentId) {
          this.loading = false;
          this.$message.error(body.msg || 'Tạo tác nhân thất bại');
          return;
        }
        // 2) gắn thiết bị bằng mã 6 số
        const rollback = (msg) => {
          Api.agent.deleteAgent(agentId, () => {});
          this.loading = false;
          this.$message.error({ message: msg || 'Mã thiết bị không đúng hoặc đã hết hạn', showClose: true });
        };
        Api.device.bindDevice(agentId, code, ({ data }) => {
          if (data && data.code === 0) {
            this.loading = false;
            this.$message.success({ message: 'Đã thêm robot! Bạn có thể đổi tên tác nhân sau.', showClose: true });
            this.$emit('confirm', res);
            this.$emit('update:visible', false);
            this.deviceCode = "";
          } else {
            rollback(data && data.msg);
          }
        }, (err) => rollback(err && err.data && err.data.msg));
      });
    },
    cancel() {
      if (this.loading) return;
      this.deviceCode = "";
      this.$emit('update:visible', false);
    },
    handleClose() {
      this.cancel();
    }
  }
}
</script>

<style scoped>
.add-agent-body {
  padding: 6px 4px 4px;
}

.add-agent-label {
  font-size: 14px;
  color: #475569;
  text-align: left;
  margin-bottom: 12px;
}

.add-agent-label .required {
  color: #f56c6c;
  margin-right: 2px;
}

.add-agent-input ::v-deep(.el-input__inner) {
  height: 40px;
  border-radius: 8px;
  border-color: #e2e8f0;
  font-size: 14px;
}

.code-input ::v-deep(.el-input__inner) {
  font-size: 22px;
  letter-spacing: 8px;
  text-align: center;
  font-family: monospace;
}

.add-agent-hint {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
  text-align: left;
}
</style>
