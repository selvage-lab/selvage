/**
 * Annotation이 포함된 샘플 Kotlin 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

import kotlin.collections.*
import kotlin.jvm.*
import javax.persistence.*
import org.springframework.beans.factory.annotation.*
import org.springframework.transaction.annotation.*
import org.springframework.web.bind.annotation.*
import org.springframework.stereotype.*

@Entity
@Component
data class UserInfo(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,
    
    @Column(nullable = false)
    val name: String,
    
    @Column
    val age: Int,
    
    @Column
    val email: String = "",
    
    @Column
    val active: Boolean = true
) {
    /**
     * 사용자 정보를 담는 데이터 클래스
     */
    
    @JvmOverloads
    @Deprecated("Use toString() instead", ReplaceWith("toString()"))
    fun getDisplayName(prefix: String = ""): String {
        /**
         * 표시용 이름 반환 (deprecated 메서드)
         */
        return "$prefix$name ($age)"
    }
}

@Entity
@Component
data class ConfigSettings(
    @Id
    val apiKey: String,
    
    @Column
    val timeout: Int = 30,
    
    @Column
    val debugMode: Boolean = false,
    
    @Column
    val maxRetries: Int = 3
) {
    /**
     * 설정 정보를 담는 데이터 클래스
     */
    
    @Transactional(readOnly = true)
    fun isDebugEnabled(): Boolean {
        /**
         * 디버그 모드 활성화 여부
         */
        return debugMode
    }
    
    companion object {
        @JvmStatic
        @Deprecated("Use constructor instead")
        @Transactional
        fun createDefault(): ConfigSettings {
            /**
             * 기본 설정 생성 (companion object 메서드)
             */
            return ConfigSettings(apiKey = "default_key")
        }
    }
}

@RestController
@RequestMapping("/api/users")
class UserController {
    /**
     * 사용자 관리 REST 컨트롤러
     */
    
    @Autowired
    private lateinit var userService: UserService
    
    @GetMapping
    @Transactional(readOnly = true)
    fun getAllUsers(): List<UserInfo> {
        /**
         * 모든 사용자 조회
         */
        return userService.findAll()
    }
    
    @PostMapping
    @Transactional
    @ResponseStatus(HttpStatus.CREATED)
    fun createUser(@RequestBody userInfo: UserInfo): UserInfo {
        /**
         * 새 사용자 생성
         */
        return userService.save(userInfo)
    }
    
    @JvmOverloads
    @Deprecated("Use standard toString", ReplaceWith("this::class.simpleName"))
    override fun toString(): String {
        /**
         * 컨트롤러 문자열 표현
         */
        return "UserController"
    }
}

@Service
class UserService {
    /**
     * 사용자 비즈니스 로직 서비스
     */
    
    @Autowired
    private lateinit var userRepository: UserRepository
    
    @Transactional(readOnly = true)
    fun findAll(): List<UserInfo> {
        return userRepository.findAll()
    }
    
    @Transactional
    fun save(userInfo: UserInfo): UserInfo {
        return userRepository.save(userInfo)
    }
    
    @JvmStatic
    @Deprecated("Use instance method instead")
    fun validateEmail(email: String): Boolean {
        /**
         * 이메일 유효성 검사 (static deprecated 메서드)
         */
        return email.contains("@")
    }
}

@Component
class DatabaseManager {
    /**
     * 데이터베이스 관리 클래스
     */
    
    private var instance: DatabaseManager? = null
    
    @PostConstruct
    fun init() {
        /**
         * 초기화 메서드
         */
        println("DatabaseManager initialized")
    }
    
    @PreDestroy
    fun cleanup() {
        /**
         * 정리 메서드
         */
        println("DatabaseManager cleanup")
    }
    
    @Async
    @Transactional
    fun connect(connectionString: String): Boolean {
        /**
         * 데이터베이스 연결
         */
        println("Connecting to: $connectionString")
        return true
    }
    
    @Async
    @Transactional(readOnly = true)
    @Cacheable("connection-status")
    fun isConnected(): Boolean {
        /**
         * 연결 상태 확인
         */
        return true
    }
}

@Component
class DataProcessor {
    
    @Async
    @Transactional
    @JvmOverloads
    fun processUserData(@Valid userInfo: UserInfo, includeEmail: Boolean = true): Map<String, Any?> {
        /**
         * 사용자 데이터 처리 메서드
         */
        val result = mutableMapOf<String, Any?>(
            "name" to userInfo.name,
            "age" to userInfo.age,
            "display" to userInfo.getDisplayName()
        )
        
        if (includeEmail) {
            result["email"] = userInfo.email
        }
        
        return result
    }
}

// 모듈 레벨 상수
@Configuration
object DefaultConfig {
    @JvmField
    val DEFAULT_CONFIG = ConfigSettings(apiKey = "test_key", debugMode = true)
}