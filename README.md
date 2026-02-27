# SCignore

스타크래프트 리마스터 채팅 차단 프로그램입니다.

Starcraft Remastered Chat Blocker.

## 요구사항 / Requirements

- Windows 10/11

## 설치 / Installation

```
⚠ 본 프로그램은 패킷을 분석하고 자동으로 명령어를 입력하는 기능을 포함하고 있어, Windows SmartScreen이나 일부 백신에서 악성코드로 오인될 수 있습니다. 프로그램은 오픈 소스로 투명하게 관리되며 어떠한 개인정보도 수집하지 않습니다.

⚠ Because this tool analyzes packets and simulates keyboard inputs, it may be flagged as a false positive by Windows SmartScreen or other antivirus software. This program is open-source and does not collect any personal data.
```

[Github Release Page](https://github.com/yjh910/SCignore/releases/tag/v1.0.0)

1. 위 릴리즈 페이지에서 `SCignore.zip` 파일을 다운로드 받습니다.
2. 압축을 해제하면 됩니다. 별도의 설치 과정은 필요 없습니다.

## 사용방법 / Usage

1. 스타크래프트 리마스터를 실행합니다.
2. `SCignore.exe`를 실행합니다.
3. **▶ Start Monitoring** 버튼을 눌러 패킷 캡처를 시작합니다.
4. 접속할 ID를 선택하면 나의 ID가 **Selected Player** 항목에 표시됩니다.

   ![u1](./docs/usage1.gif)

5. 매칭이 잡히면 상대방 ID가 **Match Opponent** 항목에 표시됩니다.

   ![u2](./docs/usage2.gif)

6. **F9**키를 누르면 `/ignore [ID]`가 자동으로 입력됩니다.

   ![u3](./docs/usage3.gif)

7. **F8**키를 눌러 차단을 해제할 수 있습니다.

   ![u4](./docs/usage4.gif)

## 개발 환경 / Dev Environment

- python 3.10.11
- Windows 10
- pydivert (packet capture)
- tkinter (GUI)
