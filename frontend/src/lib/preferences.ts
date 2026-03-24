export interface UserPreferences {
  actorName: string;
  chatSource: string;
}

const STORAGE_KEY = "tp-user-preferences";

const defaultPreferences: UserPreferences = {
  actorName: "web-user",
  chatSource: "dashboard-chat",
};

function canUseWindow(): boolean {
  return typeof window !== "undefined";
}

export function loadUserPreferences(): UserPreferences {
  if (!canUseWindow()) {
    return { ...defaultPreferences };
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { ...defaultPreferences };
  }

  try {
    const parsed = JSON.parse(raw) as Partial<UserPreferences>;
    return {
      actorName: parsed.actorName?.trim() || defaultPreferences.actorName,
      chatSource: parsed.chatSource?.trim() || defaultPreferences.chatSource,
    };
  } catch {
    return { ...defaultPreferences };
  }
}

export function saveUserPreferences(input: Partial<UserPreferences>): UserPreferences {
  const nextValue = {
    ...loadUserPreferences(),
    ...input,
  };

  if (canUseWindow()) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextValue));
  }

  return nextValue;
}
