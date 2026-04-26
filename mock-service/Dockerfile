# 多阶段构建 Dockerfile
# 第一阶段：使用 Gradle 构建应用
FROM gradle:8.5-jdk21 AS builder

WORKDIR /app

# 复制构建文件
COPY build.gradle settings.gradle ./
COPY src ./src

# 构建应用（跳过测试）
RUN gradle bootJar --no-daemon

# 第二阶段：使用 JRE 运行应用
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# 从构建阶段复制 JAR 文件
COPY --from=builder /app/build/libs/mock-service-1.0.0.jar app.jar

# 暴露端口（虽然不需要，但保留以便扩展）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# 启动应用
ENTRYPOINT ["java", "-jar", "app.jar"]
