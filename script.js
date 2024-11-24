const chatDiv = document.getElementById('chat');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

// 대화 이력 배열 초기화
let chatHistory = [];

// 메시지 전송 함수
const sendMessage = async () => {
    const userMessage = userInput.value;
    if (!userMessage) return;

    // 사용자 메시지 추가
    chatDiv.innerHTML += `<div class="user-message">사용자: ${userMessage}</div>`;
    userInput.value = '';

    // 대화 이력에 사용자 메시지 추가
    chatHistory.push({ role: 'user', content: userMessage });

    // OpenAI API 호출
    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': '개인 API키'
            },
            body: JSON.stringify({
                model: 'gpt-3.5-turbo', // 사용할 모델을 설정합니다.
                messages: chatHistory // 대화 이력을 포함
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Assistant의 응답 추가
        if (data.choices && data.choices.length > 0) {
            const assistantMessage = data.choices[0].message.content;
            chatHistory.push({ role: 'assistant', content: assistantMessage }); // 응답도 저장
            chatDiv.innerHTML += `<div class="assistant-message">Assistant: ${assistantMessage}</div>`;
        } else {
            chatDiv.innerHTML += `<div class="assistant-message">Assistant: 응답을 받을 수 없습니다.</div>`;
        }
        chatDiv.scrollTop = chatDiv.scrollHeight; // 스크롤을 아래로 이동
    } catch (error) {
        console.error('API 호출 중 오류 발생:', error);
        chatDiv.innerHTML += `<div class="assistant-message">Assistant: 오류가 발생했습니다. ${error.message}</div>`;
    }
};

// 버튼 클릭 시 메시지 전송
sendButton.onclick = sendMessage;

// 엔터 키를 눌렀을 때 메시지 전송
userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // 기본 엔터 동작 방지
        sendMessage();
    }
}); 