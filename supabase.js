// ===== supabase.js — 질문수학 DB 연결 =====
const SUPABASE_URL = 'https://nhxooqaihyhnmihlzdmn.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5oeG9vcWFpaHlobm1paGx6ZG1uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0NjU2MDgsImV4cCI6MjA4OTA0MTYwOH0.B_34NBzwEYaAWtdEoq5T__N1WRgbQytlSF1V19T_KjQ';

const { createClient } = supabase;
const db = createClient(SUPABASE_URL, SUPABASE_KEY);

// ── 프로필 저장 (로그인 시) ─────────────────────────────
// 같은 이름+역할이면 기존 ID 재사용, 없으면 신규 생성
async function dbSaveProfile(name, role, gender) {
  try {
    const { data: existing } = await db
      .from('profiles')
      .select('id')
      .eq('name', name)
      .eq('role', role)
      .maybeSingle();

    if (existing) return existing.id;

    const { data, error } = await db
      .from('profiles')
      .insert({ name, role, gender })
      .select('id')
      .single();

    if (error) throw error;
    return data.id;
  } catch (e) {
    console.warn('dbSaveProfile error:', e);
    return null;
  }
}

// ── 게임 점수 저장 ──────────────────────────────────────
async function dbSaveScore({ gameType, grade, stars, xp, score = 0, timeSec = null, errors = null, correct = null }) {
  try {
    const user = getUser();
    const userId   = user?.supabaseId || null;
    const userName = user?.name || '익명';

    await db.from('game_scores').insert({
      user_id:   userId,
      user_name: userName,
      game_type: gameType,
      grade,
      stars,
      xp,
      score,
      time_sec: timeSec,
      errors,
      correct
    });
  } catch (e) {
    console.warn('dbSaveScore error:', e);
  }
}

// ── 리더보드 조회 (게임별 TOP 10) ──────────────────────
async function dbGetLeaderboard(gameType, grade) {
  try {
    const orderCol = gameType === 'match' ? 'time_sec' : 'score';
    const asc      = gameType === 'match';

    const { data, error } = await db
      .from('game_scores')
      .select('user_name, stars, score, time_sec, correct, xp, created_at')
      .eq('game_type', gameType)
      .eq('grade', grade)
      .order(orderCol, { ascending: asc })
      .limit(10);

    if (error) throw error;
    return data || [];
  } catch (e) {
    console.warn('dbGetLeaderboard error:', e);
    return [];
  }
}

// ── 내 기록 조회 ────────────────────────────────────────
async function dbGetMyScores(gameType) {
  try {
    const user = getUser();
    if (!user?.supabaseId) return [];

    const { data, error } = await db
      .from('game_scores')
      .select('*')
      .eq('user_id', user.supabaseId)
      .eq('game_type', gameType)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) throw error;
    return data || [];
  } catch (e) {
    console.warn('dbGetMyScores error:', e);
    return [];
  }
}
