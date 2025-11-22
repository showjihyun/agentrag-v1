import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // 데모 모드: 실제 백엔드 호출 대신 시뮬레이션
    // 실제 프로덕션에서는 아래 주석을 해제하고 데모 코드를 제거하세요
    
    // Demo simulation
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return NextResponse.json({
      success: true,
      result: {
        content: `Demo response: I received your message "${body.parameters?.user_message || 'Hello'}". This is a simulated response. To use real AI, configure the backend connection.`,
        model: body.parameters?.model || 'demo',
        provider: body.parameters?.provider || 'demo',
      },
      execution_time: 1.0,
    });
    
    /* Production code - uncomment when backend is ready:
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/agent-builder/tool-execution/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization') && {
          'Authorization': request.headers.get('authorization')!,
        }),
      },
      body: JSON.stringify({
        tool_name: body.tool_id || 'ai_agent',
        parameters: body.parameters,
        config: body.credentials || {},
      }),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
    */
  } catch (error) {
    console.error('Tool execution proxy error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to execute tool' 
      },
      { status: 500 }
    );
  }
}
