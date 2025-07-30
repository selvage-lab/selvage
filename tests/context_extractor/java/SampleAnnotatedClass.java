/**
 * Annotation이 포함된 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다.
 */

import java.util.*;
import javax.persistence.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.transaction.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.stereotype.*;

@Entity
@Component
public class UserInfo {
    /**
     * 사용자 정보를 담는 엔티티 클래스
     */
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column
    private int age;
    
    @Column
    private String email;
    
    @Column
    private boolean active = true;
    
    @Autowired
    private UserService userService;
    
    public UserInfo() {
    }
    
    public UserInfo(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    @Override
    public String toString() {
        /**
         * 객체 문자열 표현 반환
         */
        return String.format("UserInfo{name='%s', age=%d}", name, age);
    }
}

@Entity
@Component  
public class ConfigSettings {
    /**
     * 설정 정보를 담는 엔티티 클래스
     */
    
    @Id
    private String apiKey;
    
    @Column
    private int timeout = 30;
    
    @Column
    private boolean debugMode = false;
    
    @Column
    private int maxRetries = 3;
    
    @Transactional(readOnly = true)
    public boolean isDebugEnabled() {
        /**
         * 디버그 모드 활성화 여부
         */
        return debugMode;
    }
    
    @Deprecated
    @Transactional
    public static ConfigSettings createDefault() {
        /**
         * 기본 설정 생성 (deprecated 메서드)
         */
        ConfigSettings config = new ConfigSettings();
        config.apiKey = "default_key";
        return config;
    }
}

@RestController
@RequestMapping("/api/users")
public class UserController {
    /**
     * 사용자 관리 REST 컨트롤러
     */
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    @Transactional(readOnly = true)
    public List<UserInfo> getAllUsers() {
        /**
         * 모든 사용자 조회
         */
        return userService.findAll();
    }
    
    @PostMapping
    @Transactional
    @ResponseStatus(HttpStatus.CREATED)
    public UserInfo createUser(@RequestBody UserInfo userInfo) {
        /**
         * 새 사용자 생성
         */
        return userService.save(userInfo);
    }
    
    @Override
    @Deprecated
    public String toString() {
        /**
         * 컨트롤러 문자열 표현
         */
        return "UserController";
    }
}

@Service
public class UserService {
    /**
     * 사용자 비즈니스 로직 서비스
     */
    
    @Autowired
    private UserRepository userRepository;
    
    @Transactional(readOnly = true)
    public List<UserInfo> findAll() {
        return userRepository.findAll();
    }
    
    @Transactional
    public UserInfo save(UserInfo userInfo) {
        return userRepository.save(userInfo);
    }
    
    @Override
    @Deprecated
    public boolean equals(Object obj) {
        /**
         * 서비스 동등성 비교 (deprecated)
         */
        return super.equals(obj);
    }
}

@Component
public class DatabaseManager {
    /**
     * 데이터베이스 관리 클래스
     */
    
    private static DatabaseManager instance;
    
    @PostConstruct
    public void init() {
        /**
         * 초기화 메서드
         */
        System.out.println("DatabaseManager initialized");
    }
    
    @PreDestroy
    public void cleanup() {
        /**
         * 정리 메서드
         */
        System.out.println("DatabaseManager cleanup");
    }
    
    @Async
    @Transactional
    public boolean connect(String connectionString) {
        /**
         * 데이터베이스 연결
         */
        System.out.println("Connecting to: " + connectionString);
        return true;
    }
    
    @Async
    @Transactional(readOnly = true)
    @Cacheable("connection-status")
    public boolean isConnected() {
        /**
         * 연결 상태 확인
         */
        return true;
    }
}

@Component
public class DataProcessor {
    
    @Async
    @Transactional
    public Map<String, Object> processUserData(@Valid UserInfo userInfo) {
        /**
         * 사용자 데이터 처리 메서드
         */
        Map<String, Object> result = new HashMap<>();
        result.put("name", userInfo.name);
        result.put("age", userInfo.age);
        result.put("display", userInfo.toString());
        return result;
    }
}

// 모듈 레벨 상수
@Configuration
class DefaultConfig {
    public static final ConfigSettings DEFAULT_CONFIG = new ConfigSettings();
}