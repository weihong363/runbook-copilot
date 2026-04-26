package com.ironion.mock;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 日志模拟器
 * 负责生成各种生产环境场景的模拟日志
 */
@Slf4j
@Component
public class LogSimulator {

    // API路径列表
    private static final String[] API_PATHS = {
            "/api/orders",
            "/api/payments",
            "/api/inventory",
            "/api/users",
            "/api/workflows",
            "/api/notifications"
    };

    // HTTP方法列表
    private static final String[] HTTP_METHODS = {"GET", "POST", "PUT", "DELETE"};

    // 下游服务名称列表
    private static final String[] DOWNSTREAM_SERVICES = {
            "payment-service",
            "inventory-service",
            "user-service",
            "notification-service",
            "workflow-engine"
    };

    // 用户ID列表
    private static final String[] USER_IDS = {
            "user_88321", "user_92456", "user_71234", "user_65789", "user_54321"
    };

    // 区域列表
    private static final String[] REGIONS = {"cn-beijing", "cn-shanghai", "cn-guangzhou", "cn-shenzhen"};

    /**
     * 生成随机UUID作为订单ID或请求ID
     */
    private String generateId() {
        return UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    /**
     * 生成追踪ID（16位十六进制）
     */
    private String generateTraceId() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 16);
    }

    /**
     * 生成跨度ID（16位十六进制）
     */
    private String generateSpanId() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 16);
    }

    /**
     * 生成随机延迟时间（毫秒）
     */
    private int generateLatency(int min, int max) {
        return ThreadLocalRandom.current().nextInt(min, max);
    }

    /**
     * 选择随机API路径
     */
    private String randomPath() {
        return API_PATHS[ThreadLocalRandom.current().nextInt(API_PATHS.length)];
    }

    /**
     * 选择随机HTTP方法
     */
    private String randomMethod() {
        return HTTP_METHODS[ThreadLocalRandom.current().nextInt(HTTP_METHODS.length)];
    }

    /**
     * 选择随机下游服务
     */
    private String randomService() {
        return DOWNSTREAM_SERVICES[ThreadLocalRandom.current().nextInt(DOWNSTREAM_SERVICES.length)];
    }

    /**
     * 选择随机用户ID
     */
    private String randomUserId() {
        return USER_IDS[ThreadLocalRandom.current().nextInt(USER_IDS.length)];
    }

    /**
     * 选择随机区域
     */
    private String randomRegion() {
        return REGIONS[ThreadLocalRandom.current().nextInt(REGIONS.length)];
    }

    /**
     * 主方法：执行日志模拟
     * 根据概率随机选择场景并生成对应日志
     */
    public void simulate() {
        ScenarioType scenario = ScenarioType.randomScenario();
        
        // 设置追踪上下文
        String traceId = generateTraceId();
        String spanId = generateSpanId();
        LogContext.setContext(traceId, spanId);

        try {
            switch (scenario) {
                case NORMAL_REQUEST -> logNormalRequest();
                case SLOW_REQUEST -> logSlowRequest();
                case DATABASE_TIMEOUT -> logDatabaseTimeout();
                case DOWNSTREAM_TIMEOUT -> logDownstreamTimeout();
                case NULL_POINTER -> logNullPointerException();
                case INVALID_ARGUMENT -> logInvalidArgument();
                case BUSINESS_DATA_ERROR -> logBusinessDataError();
                case ORDER_STATUS_MISMATCH -> logOrderStatusMismatch();
                case INVENTORY_NOT_ENOUGH -> logInventoryNotEnough();
                case PAYMENT_STATUS_ERROR -> logPaymentStatusError();
                case WORKFLOW_BLOCKED -> logWorkflowBlocked();
                case RETRYING -> logRetrying();
                case RETRY_FAILED -> logRetryFailed();
                case THREAD_POOL_PRESSURE -> logThreadPoolPressure();
            }
        } catch (Exception e) {
            log.error("场景=日志模拟异常, 错误={}", e.getMessage(), e);
        } finally {
            // 清除追踪上下文
            LogContext.clearContext();
        }
    }

    /**
     * 场景1：正常请求
     * 模拟正常的API调用，返回成功状态
     */
    private void logNormalRequest() {
        String orderId = generateId();
        String userId = randomUserId();
        String path = randomPath();
        String method = randomMethod();
        int latency = generateLatency(50, 300);
        String region = randomRegion();

        log.info("用户={}, 订单={}, 方法={}, 路径={}, 状态=200, 延迟={}ms, 区域={}",
                userId, orderId, method, path, latency, region);
    }

    /**
     * 场景2：慢请求
     * 模拟响应时间过长的请求，可能是性能问题
     */
    private void logSlowRequest() {
        String orderId = generateId();
        String userId = randomUserId();
        String path = randomPath();
        String method = randomMethod();
        int latency = generateLatency(1000, 5000);
        String region = randomRegion();

        log.warn("用户={}, 订单={}, 方法={}, 路径={}, 状态=200, 延迟={}ms, 阈值=1000ms, 区域={}, 消息=慢请求检测", 
                userId, orderId, method, path, latency, region);
    }

    /**
     * 场景3：数据库超时
     * 模拟数据库查询或连接超时，包含完整异常堆栈
     */
    private void logDatabaseTimeout() {
        String orderId = generateId();
        String userId = randomUserId();
        int timeout = generateLatency(5000, 30000);
        String region = randomRegion();

        RuntimeException exception = new RuntimeException(
                String.format("数据库查询超时，耗时 %dms", timeout),
                new java.sql.SQLException("连接超时", "08S01")
        );

        log.error("用户={}, 订单={}, 路径=/api/orders, 状态=504, 错误码=B0001, 数据库主机=mysql-primary:3306, 查询=SELECT * FROM orders WHERE id=?, 超时={}ms, 区域={}, 错误={}",
                userId, orderId, timeout, region, exception.getMessage(), exception);
    }

    /**
     * 场景4：下游服务超时
     * 模拟调用微服务依赖时超时，包含完整异常堆栈
     */
    private void logDownstreamTimeout() {
        String orderId = generateId();
        String userId = randomUserId();
        String service = randomService();
        int timeout = generateLatency(3000, 15000);
        String region = randomRegion();

        RuntimeException exception = new RuntimeException(
                String.format("下游服务 [%s] 超时，耗时 %dms", service, timeout),
                new java.net.SocketTimeoutException("读取超时")
        );

        log.error("用户={}, 订单={}, 下游服务={}, 状态=504, 错误码=C0001, 端点=https://{}:8080/api/v1/resource, 超时={}ms, 区域={}, 错误={}",
                userId, orderId, service, service, timeout, region, exception.getMessage(), exception);
    }

    /**
     * 场景5：空指针异常
     * 模拟代码中的NPE错误，包含完整异常堆栈
     */
    private void logNullPointerException() {
        String orderId = generateId();
        String userId = randomUserId();
        String path = randomPath();
        String region = randomRegion();

        NullPointerException exception = new NullPointerException(
                "无法调用 \"com.example.model.Order.getAmount()\"，因为 \"order\" 为 null"
        );

        log.error("用户={}, 订单={}, 路径={}, 状态=500, 错误码=B0002, 区域={}, 错误={}",
                userId, orderId, path, region, exception.getMessage(), exception);
    }

    /**
     * 场景6：无效参数
     * 模拟参数校验失败
     */
    private void logInvalidArgument() {
        String orderId = generateId();
        String userId = randomUserId();
        String path = randomPath();
        String field = new String[]{"金额", "数量", "用户ID", "商品ID"}[ThreadLocalRandom.current().nextInt(4)];
        String region = randomRegion();

        log.warn("用户={}, 订单={}, 路径={}, 状态=400, 错误码=A0001, 字段={}, 校验错误=true, 区域={}, 消息=无效参数: {} 是必填项",
                userId, orderId, path, field, region, field);
    }

    /**
     * 场景7：业务数据错误
     * 模拟数据不一致或业务规则违反
     */
    private void logBusinessDataError() {
        String orderId = generateId();
        String userId = randomUserId();
        String path = randomPath();
        String region = randomRegion();

        IllegalStateException exception = new IllegalStateException(
                "检测到业务数据不一致: 预期金额=100.00, 实际金额=95.50"
        );

        log.error("用户={}, 订单={}, 路径={}, 状态=500, 错误码=B0003, 预期金额=100.00, 实际金额=95.50, 货币=CNY, 区域={}, 错误={}",
                userId, orderId, path, region, exception.getMessage(), exception);
    }

    /**
     * 场景8：订单状态不匹配
     * 模拟订单流转过程中的状态异常
     */
    private void logOrderStatusMismatch() {
        String orderId = generateId();
        String userId = randomUserId();
        String currentState = new String[]{"待处理", "已支付", "已发货", "已取消"}[ThreadLocalRandom.current().nextInt(4)];
        String expectedState = new String[]{"已支付", "已发货", "已送达", "已完成"}[ThreadLocalRandom.current().nextInt(4)];
        String region = randomRegion();

        IllegalStateException exception = new IllegalStateException(
                String.format("订单状态不匹配: 当前状态=%s, 期望状态=%s", currentState, expectedState)
        );

        log.error("用户={}, 订单={}, 路径=/api/orders, 状态=409, 错误码=B0004, 当前状态={}, 期望状态={}, 区域={}, 错误={}",
                userId, orderId, currentState, expectedState, region, exception.getMessage(), exception);
    }

    /**
     * 场景9：库存不足
     * 模拟库存扣减失败
     */
    private void logInventoryNotEnough() {
        String orderId = generateId();
        String userId = randomUserId();
        String productId = generateId();
        int requested = ThreadLocalRandom.current().nextInt(10, 100);
        int available = ThreadLocalRandom.current().nextInt(0, requested);
        String region = randomRegion();

        log.warn("用户={}, 订单={}, 路径=/api/inventory, 状态=400, 错误码=A0002, 商品ID={}, 请求数量={}, 可用数量={}, 区域={}, 消息=库存不足",
                userId, orderId, productId, requested, available, region);
    }

    /**
     * 场景10：支付状态错误
     * 模拟支付流程中的状态异常
     */
    private void logPaymentStatusError() {
        String orderId = generateId();
        String userId = randomUserId();
        String paymentId = generateId();
        String paymentStatus = new String[]{"失败", "超时", "已退款", "未知"}[ThreadLocalRandom.current().nextInt(4)];
        String region = randomRegion();

        RuntimeException exception = new RuntimeException(
                String.format("支付状态错误: 支付状态=%s, 期望状态=成功", paymentStatus)
        );

        log.error("用户={}, 订单={}, 支付ID={}, 路径=/api/payments, 状态=500, 错误码=C0002, 支付状态={}, 期望状态=成功, 区域={}, 错误={}",
                userId, orderId, paymentId, paymentStatus, region, exception.getMessage(), exception);
    }

    /**
     * 场景11：工作流阻塞
     * 模拟业务流程引擎中的阻塞
     */
    private void logWorkflowBlocked() {
        String orderId = generateId();
        String userId = randomUserId();
        String workflowId = generateId();
        String blockedAt = new String[]{"审批", "支付验证", "库存检查", "发货确认"}[ThreadLocalRandom.current().nextInt(4)];
        int waitingTime = generateLatency(30, 300);
        String region = randomRegion();

        RuntimeException exception = new RuntimeException(
                String.format("工作流在阶段 [%s] 阻塞，等待 %d 分钟", blockedAt, waitingTime)
        );

        log.error("用户={}, 订单={}, 工作流ID={}, 路径=/api/workflows, 状态=500, 错误码=B0005, 阻塞阶段={}, 等待时间={}分钟, 区域={}, 错误={}",
                userId, orderId, workflowId, blockedAt, waitingTime, region, exception.getMessage(), exception);
    }

    /**
     * 场景12：重试中
     * 模拟临时故障后的重试机制
     */
    private void logRetrying() {
        String orderId = generateId();
        String userId = randomUserId();
        String service = randomService();
        int attempt = ThreadLocalRandom.current().nextInt(1, 4);
        int maxRetries = 3;
        int retryDelay = generateLatency(1000, 5000);
        String region = randomRegion();

        log.warn("用户={}, 订单={}, 下游服务={}, 尝试次数={}/{}, 错误=连接被拒绝，重试中..., 重试延迟={}ms, 区域={}, 消息=重试尝试 {} of {}",
                userId, orderId, service, attempt, maxRetries, retryDelay, region, attempt, maxRetries);
    }

    /**
     * 场景13：重试失败
     * 模拟多次重试后仍然失败
     */
    private void logRetryFailed() {
        String orderId = generateId();
        String userId = randomUserId();
        String service = randomService();
        int maxRetries = 3;
        String region = randomRegion();

        RuntimeException exception = new RuntimeException(
                String.format("服务 [%s] 在 %d 次重试后仍失败", service, maxRetries)
        );

        log.error("用户={}, 订单={}, 下游服务={}, 尝试次数={}/{}, 状态=503, 错误码=C0003, 熔断器=开启, 区域={}, 错误={}",
                userId, orderId, service, maxRetries, maxRetries, region, exception.getMessage(), exception);
    }

    /**
     * 场景14：线程池压力
     * 模拟高负载下线程池资源紧张
     */
    private void logThreadPoolPressure() {
        String orderId = generateId();
        String poolName = new String[]{"http-nio", "task-executor", "async-worker", "db-pool"}[ThreadLocalRandom.current().nextInt(4)];
        int activeThreads = ThreadLocalRandom.current().nextInt(80, 100);
        int maxThreads = 100;
        int queueSize = ThreadLocalRandom.current().nextInt(100, 500);
        int saturation = (activeThreads * 100 / maxThreads);
        String region = randomRegion();

        log.warn("订单={}, 线程池={}, 活跃线程={}/{}, 队列大小={}, 饱和度={}%, 区域={}, 消息=线程池压力过大",
                orderId, poolName, activeThreads, maxThreads, queueSize, saturation, region);
    }
}
