DROP DATABASE LEMONA_GMP;

CREATE DATABASE LEMONA_GMP;

USE LEMONA_GMP;

CREATE TABLE USER (
    USER_ID VARCHAR(50) PRIMARY KEY,
    PW VARCHAR(255),
    NAME VARCHAR(100),
    DIVISION VARCHAR(100),
    STATUS BOOLEAN DEFAULT TRUE,
    ROLE_ID INT,
    PW_UPDATE_DT DATE,
    CREATE_DT DATE,
    UPDATE_DT DATE
);

CREATE TABLE COMMENT (
    COMMENT_ID INT PRIMARY KEY AUTO_INCREMENT,
    CONTENT VARCHAR(1000),
    USER_ID VARCHAR(50)
);

CREATE TABLE ROLE (
    ROLE_ID INT PRIMARY KEY AUTO_INCREMENT,
    ROLE_NAME VARCHAR(50)
);

CREATE TABLE ACCESS (
    ACCESS_ID INT PRIMARY KEY AUTO_INCREMENT,
    ROLE_ID INT NOT NULL,
    PAGE_ID INT NOT NULL
);

CREATE TABLE PAGE (
    PAGE_ID INT PRIMARY KEY AUTO_INCREMENT,
    PAGE_LINK VARCHAR(100),
    MENU_NAME VARCHAR(100),
    PAGE_NAME VARCHAR(100)
);

CREATE TABLE EQUIPMENT_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE ALARM_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE REPORT_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE LOGIN_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE USER_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE DATA_HISTORY (
    ID INT PRIMARY KEY AUTO_INCREMENT,
	CONTENT VARCHAR(255),
    USER_ID VARCHAR(50),
    COMMENT_ID int,
    CREATE_DT DATETIME
);

CREATE TABLE ALARM_LIST (
    ID INT PRIMARY KEY,
	CONTENT VARCHAR(255)
);

ALTER TABLE USER 
ADD CONSTRAINT FK_USER_ROLE 
FOREIGN KEY (ROLE_ID) REFERENCES ROLE(ROLE_ID);

ALTER TABLE COMMENT 
ADD CONSTRAINT FK_COMMENT_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE ACCESS 
ADD CONSTRAINT FK_ACCESS_ROLE 
FOREIGN KEY (ROLE_ID) REFERENCES ROLE(ROLE_ID);

ALTER TABLE ACCESS 
ADD CONSTRAINT FK_ACCESS_PAGE 
FOREIGN KEY (PAGE_ID) REFERENCES PAGE(PAGE_ID);

ALTER TABLE EQUIPMENT_HISTORY 
ADD CONSTRAINT FK_EQUIPMENT_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE ALARM_HISTORY
ADD CONSTRAINT FK_ALARM_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE REPORT_HISTORY
ADD CONSTRAINT FK_REPORT_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE LOGIN_HISTORY
ADD CONSTRAINT FK_LOGIN_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE USER_HISTORY
ADD CONSTRAINT FK_USER_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE DATA_HISTORY
ADD CONSTRAINT FK_DATA_HISTORY_USER
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

ALTER TABLE EQUIPMENT_HISTORY 
ADD CONSTRAINT FK_EQUIPMENT_HISTORY_COMMENT
FOREIGN KEY (COMMENT_ID) REFERENCES COMMENT(COMMENT_ID);

ALTER TABLE ALARM_HISTORY
ADD CONSTRAINT FK_ALARM_HISTORY_COMMENT
FOREIGN KEY (COMMENT_ID) REFERENCES COMMENT(COMMENT_ID);

ALTER TABLE REPORT_HISTORY
ADD CONSTRAINT FK_REPORT_HISTORY_COMMENT
FOREIGN KEY (COMMENT_ID) REFERENCES COMMENT(COMMENT_ID);

ALTER TABLE LOGIN_HISTORY
ADD CONSTRAINT FK_LOGIN_HISTORY_COMMENT
FOREIGN KEY (COMMENT_ID) REFERENCES COMMENT(COMMENT_ID);

ALTER TABLE USER_HISTORY
ADD CONSTRAINT FK_USER_HISTORY_COMMENT
FOREIGN KEY (COMMENT_ID) REFERENCES COMMENT(COMMENT_ID);

ALTER TABLE DATA_HISTORY
ADD CONSTRAINT FK_DATA_HISTORY_COMMENT
FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID);

INSERT INTO ROLE (ROLE_NAME) VALUES 
('ROOT'),
('ADMIN'), 
('MANAGER'),
('USER');

INSERT INTO PAGE (PAGE_LINK, MENU_NAME, PAGE_NAME) VALUES
('equipment-history', '이력 조회', '설비 가동 이력 조회'), -- 1
('alarm-history', '이력 조회', '설비 알람 이력 조회'),  -- 2
('report-history', '이력 조회', '보고서 생성 이력 조회'), -- 3
('login-history', '이력 조회', '접속 이력 조회'), -- 4
('user-history', '이력 조회', '사용자 관리 이력 조회'), -- 5
('data-history', '이력 조회', '데이터 관리 이력 조회'), -- 6
('user-create', '사용자 관리', '사용자 생성'), -- 7
('user-update', '사용자 관리', '사용자 수정'), -- 8
('access-update', '사용자 관리', '권한별 접근 가능 페이지 관리'), -- 9
('password-change', '사용자 관리', '비밀번호 변경'), -- 10
('audit-trail', '감사 추적', 'Audit Trail'), -- 11
('backup-restore', '데이터 관리', '데이터 백업/복원'), -- 12
('plc-test', 'PLC 테스트', 'PLC 통신 테스트'); -- 13

INSERT INTO ACCESS (ROLE_ID, PAGE_ID) VALUES
('1', '7'),
('1', '13'),
('2', '1'),
('2', '2'),
('2', '3'),
('2', '4'),
('2', '5'),
('2', '6'),
('2', '7'),
('2', '8'),
('2', '9'),
('2', '10'),
('2', '11'),
('2', '12'),
('3', '1'),
('3', '2'),
('3', '3'),
('3', '4'),
('3', '5'),
('3', '6'),
('3', '10'),
('3', '11'),
('4', '1'),
('4', '2'),
('4', '3'),
('4', '4'),
('4', '5'),
('4', '6'),
('4', '10'),
('4', '11');

INSERT INTO USER (USER_ID, PW, NAME, DIVISION, STATUS, ROLE_ID, PW_UPDATE_DT, CREATE_DT, UPDATE_DT) VALUES 
('root', '6cbefd8960d511540f34779628ef4e5a55b758d3be5749cd8878a09b348c052b', '시스템 관리자', 'IT부서', TRUE, 1, CURDATE(), CURDATE(), CURDATE()); 
INSERT INTO USER (USER_ID, PW, NAME, DIVISION, STATUS, ROLE_ID, PW_UPDATE_DT, CREATE_DT, UPDATE_DT) VALUES 
('admin', '6cbefd8960d511540f34779628ef4e5a55b758d3be5749cd8878a09b348c052b','관리자', '관리부', TRUE, 2, NULL,CURDATE(), CURDATE());
INSERT INTO USER (USER_ID, PW, NAME, DIVISION, STATUS, ROLE_ID, PW_UPDATE_DT, CREATE_DT, UPDATE_DT) VALUES 
('manager', '6cbefd8960d511540f34779628ef4e5a55b758d3be5749cd8878a09b348c052b','매니저', '생산부', TRUE, 3, NULL,CURDATE(), CURDATE());
INSERT INTO USER (USER_ID, PW, NAME, DIVISION, STATUS, ROLE_ID, PW_UPDATE_DT, CREATE_DT, UPDATE_DT) VALUES 
('user', '6cbefd8960d511540f34779628ef4e5a55b758d3be5749cd8878a09b348c052b','일반사용자', '품질관리부', TRUE, 4, NULL,CURDATE(), CURDATE());

INSERT INTO ALARM_LIST (ID, CONTENT) VALUES
(1, '1축 투입 분리 서보 알람 !!'),
(2, '2축 간격조절 이송 서보 알람 !!'),
(7, '1축 투입 분리 서보 LIMIT + 알람 !!'),
(8, '1축 투입 분리 서보 LIMIT - 알람 !!'),
(9, '2축 간격조절 이송 서보 LIMIT + 알람 !!'),
(10, '2축 간격조절 이송 서보 LIMIT - 알람 !!'),
(15, 'OP 비상정지 알람 !! [R60004]'),
(16, '박스 투입 컨베어 비상정지 알람 !! [R60006]'),
(20, '메인 에어 센서 알람 !! [R60005]'),
(23, '도어1 열림 알람 !! [R60010]'),
(24, '도어2 열림 알람 !! [R60011]'),
(25, '도어3 열림 알람 !! [R60012]'),
(26, '도어4 열림 알람 !! [R60013]'),
(30, '로봇 핸드1 흡착 패드 교체주기 알람 !!'),
(31, '로봇 핸드2 흡착 패드 교체주기 알람 !!'),
(36, '수량선별 병 공급 지연 알람 !! [R1000][R1005~9]'),
(37, '수량선별 병 걸림 알람 !! [R1000][R1005~9]'),
(38, '수량선별 이송 포인트 제품 이상 !! 제품 및 공정 모니터 조취 요망 !!'),
(41, '수량선별 스토퍼 상승 알람 !! [R1100]'),
(42, '수량선별 스토퍼 하강 알람 !! [R1101]'),
(43, '수량선별 선별 후진 알람 !! [R1102]'),
(44, '수량선별 선별 전진 알람 !! [R1103]'),
(45, '수량선별 선별 하강 알람 !! [R1104]'),
(46, '수량선별 선별 상승 알람 !! [R1105]'),
(49, '간격조절 유닛 전진 병 간섭 !! [R1107]'),
(50, '간격 조절 이송 포인트 제품 이상 !! 제품 및 공정 모니터 조취 요망 !!'),
(51, '간격조절 병 유무 센서 이상 !! [R1200]'),
(52, '픽업정렬 병 유무 센서 이상 !! [R1201]'),
(53, '간격조절 스토퍼 하강 알람 !! [R1202]'),
(54, '간격조절 스토퍼 상승 알람 !! [R1203]'),
(55, '간격조절 하강 알람 !! [R1204]'),
(56, '간격조절 상승 알람 !! [R1205]'),
(57, '간격조절 우측 벌림 알람 !! [R1206]'),
(58, '간격조절 우측 좁힘 알람 !! [R1207]'),
(59, '간격조절 좌측 벌림 알람 !! [R1208]'),
(60, '간격조절 좌측 좁힘 알람 !! [R1209]'),
(61, '간격조절 픽업 가이드 후진 알람 !! [R1210]'),
(62, '간격조절 픽업 가이드 전진 알람 !! [R1211]'),
(63, '간격조절 픽업 가이드 전면 좁힘 알람 !! [R1212]'),
(64, '간격조절 픽업 가이드 전면 벌림 알람 !! [R1213]'),
(65, '간격조절 픽업 가이드 후면 좁힘 알람 !! [R1214]'),
(66, '간격조절 픽업 가이드 후면 벌림 알람 !! [R1215]'),
(67, '박스 공급 지연 알람 !! [R1301][R1302]'),
(68, '박스 버퍼 박스 걸림 !! [R1301]'),
(69, '병 박스 포장부 박스 걸림 !! [R1303]'),
(72, '박스 투입 레일 좁힘 알람 !! [R1306]'),
(73, '박스 투입 레일 벌림 알람 !! [R1307]'),
(74, '박스 배출 레일 좁힘 알람 !! [R1308]'),
(75, '박스 배출 레일 벌림 알람 !! [R1309]'),
(76, '박스1 스토퍼 하강 알람 !! [R1310]'),
(77, '박스1 스토퍼 상승 알람 !! [R1311]'),
(78, '박스2 고정 좁힘 알람 !! [R1312]'),
(79, '박스2 고정 벌림 알람 !! [R1313]'),
(80, '병 포장 박스 스토퍼 하강 알람 !! [R1314]'),
(81, '병 포장 박스 스토퍼 상승 알람 !! [R1315]'),
(83, '비전 Ready 신호 미확인 알람 !! [R1110]'),
(84, '비전 NG 알람 !!'),
(87, '로봇 READY OFF 신호 이상 !!'),
(88, '로봇 ALARM 신호 이상 !!'),
(89, '로봇 원점 이상 !!'),
(91, '로봇 PING 통신 이상 !!'),
(93, '로봇 병 픽업 실패 !! [R1201] 제품 제거 및 공정 모니터 조취 요망 !!'),
(95, '로봇 핸드1 거치대 안착 확인 알람 !! [R1400]'),
(96, '로봇 핸드2 거치대 안착 확인 알람 !! [R1401]'),
(97, '로봇 핸드1 체결 확인 알람 !! [R1402]'),
(98, '로봇 핸드2 체결 확인 알람 !! [R1403]'),
(99, '로봇 핸드 Lock Off 확인 알람 !! [R1404]'),
(100, '로봇 핸드 Lock On 확인 알람 !! [R1405]'),
(101, '로봇 핸드1 실린더 하강 알람 !! [R1406]'),
(102, '로봇 핸드1 실린더 상승 알람 !! [R1407]'),
(105, 'PC 통신 이상 알람 !! [PING 체크]'),
(106, 'PC 설비 상태 변경 이벤트 읽기 신호 미확인 알람 !!'),
(107, 'PC 로그인 권한 미확인 알람 !!'),
(108, 'PC 터치 현재 화면 변경 이벤트 읽기 신호 미확인 알람 !!'),
(109, 'PC 알람 이벤트 읽기 신호 미확인 알람 !!'),
(110, 'PC 일 생산 수량 이벤트 읽기 신호 미확인 알람 !!'),
(111, 'PC 현재 모델 변경 이벤트 읽기 신호 미확인 알람 !!');

select * from login_history;
select * from equipment_history;
select * from alarm_history;