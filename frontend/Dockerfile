# ============================================================
# 职路AI - 前端Dockerfile
# Node.js构建 + Nginx服务容器
# ============================================================

# ============================================================
# 阶段1: 使用Node.js构建前端应用
# ============================================================
FROM node:22-alpine AS builder

WORKDIR /app

# 复制依赖文件并安装
COPY package*.json ./
RUN npm ci --include=dev && npm cache clean --force

# 复制全部源代码并构建
COPY . .
RUN npm run build

# ============================================================
# 阶段2: 使用Nginx提供静态文件服务
# ============================================================
FROM nginx:alpine AS production

# 复制构建产物到Nginx目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
