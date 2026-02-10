import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import {
  User,
  Lock,
  Key,
  Save,
  Trash2,
  Eye,
  EyeOff,
  Check,
  AlertCircle,
} from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';

interface APIKeyInfo {
  provider: string;
  masked_key: string;
  created_at: string;
}

const PROVIDERS = [
  { value: 'anthropic', label: 'Anthropic (Claude)', icon: '🟣' },
  { value: 'openai', label: 'OpenAI (GPT-4)', icon: '🟢' },
  { value: 'gemini', label: 'Google (Gemini)', icon: '🔵' },
];

export default function SettingsPage() {
  const { token } = useAuth();

  // Profile state
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // API Keys state
  const [apiKeys, setApiKeys] = useState<APIKeyInfo[]>([]);
  const [keysLoading, setKeysLoading] = useState(true);
  const [newKeyProvider, setNewKeyProvider] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [keySaving, setKeySaving] = useState(false);
  const [keyMessage, setKeyMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // --- Profile ---

  const fetchProfile = useCallback(async () => {
    if (!token) return;
    setProfileLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setEmail(data.email);
      }
    } catch (err) {
      console.error('Failed to fetch profile:', err);
    } finally {
      setProfileLoading(false);
    }
  }, [token]);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setProfileSaving(true);
    setProfileMessage(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
        }),
      });

      if (res.ok) {
        setProfileMessage({ type: 'success', text: 'Profile updated successfully' });
      } else {
        const errorData = await res.json();
        setProfileMessage({ type: 'error', text: errorData.detail || 'Failed to update profile' });
      }
    } catch {
      setProfileMessage({ type: 'error', text: 'Failed to update profile' });
    } finally {
      setProfileSaving(false);
    }
  };

  // --- Password ---

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMessage({ type: 'error', text: 'Password must be at least 8 characters' });
      return;
    }

    setPasswordSaving(true);
    setPasswordMessage(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (res.ok) {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordMessage({ type: 'success', text: 'Password changed successfully' });
      } else {
        const errorData = await res.json();
        setPasswordMessage({ type: 'error', text: errorData.detail || 'Failed to change password' });
      }
    } catch {
      setPasswordMessage({ type: 'error', text: 'Failed to change password' });
    } finally {
      setPasswordSaving(false);
    }
  };

  // --- API Keys ---

  const fetchApiKeys = useCallback(async () => {
    if (!token) return;
    setKeysLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/api-keys`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data);
      }
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    } finally {
      setKeysLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchProfile();
    fetchApiKeys();
  }, [fetchProfile, fetchApiKeys]);

  const saveApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newKeyProvider || !newKeyValue) return;

    setKeySaving(true);
    setKeyMessage(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider: newKeyProvider,
          api_key: newKeyValue,
        }),
      });

      if (res.ok) {
        setNewKeyProvider('');
        setNewKeyValue('');
        setShowKeyInput(false);
        setKeyMessage({ type: 'success', text: 'API key saved successfully' });
        fetchApiKeys();
      } else {
        const errorData = await res.json();
        setKeyMessage({ type: 'error', text: errorData.detail || 'Failed to save API key' });
      }
    } catch {
      setKeyMessage({ type: 'error', text: 'Failed to save API key' });
    } finally {
      setKeySaving(false);
    }
  };

  const deleteApiKey = async (provider: string) => {
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/settings/api-keys/${provider}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        setApiKeys((prev) => prev.filter((k) => k.provider !== provider));
        setKeyMessage({ type: 'success', text: `API key for ${provider} removed` });
      }
    } catch (err) {
      console.error('Failed to delete API key:', err);
    }
  };

  const getProviderInfo = (provider: string) => {
    return PROVIDERS.find((p) => p.value === provider) || { value: provider, label: provider, icon: '🔑' };
  };

  return (
    <PageContainer
      maxWidth="narrow"
      title="Settings"
      description="Manage your account settings and preferences"
    >

        {/* ───── Profile Section ───── */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Profile</h2>
              <p className="text-sm text-muted-foreground">Manage your account details</p>
            </div>
          </div>

          {profileLoading ? (
            <div className="text-center py-6 text-muted-foreground">Loading profile...</div>
          ) : (
            <form onSubmit={saveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="First name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Last name"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@example.com"
                />
              </div>

              {profileMessage && (
                <div
                  className={`text-sm flex items-center gap-2 p-3 rounded ${
                    profileMessage.type === 'success'
                      ? 'text-green-400 bg-green-500/10 border border-green-500/20'
                      : 'text-destructive bg-destructive/10 border border-destructive/20'
                  }`}
                >
                  {profileMessage.type === 'success' ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <AlertCircle className="w-4 h-4" />
                  )}
                  {profileMessage.text}
                </div>
              )}

              <div className="flex justify-end">
                <Button type="submit" disabled={profileSaving} className="gap-2">
                  <Save className="w-4 h-4" />
                  {profileSaving ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          )}
        </Card>

        {/* ───── Password Section ───── */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-orange-500/10 flex items-center justify-center">
              <Lock className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Password</h2>
              <p className="text-sm text-muted-foreground">Change your account password</p>
            </div>
          </div>

          <form onSubmit={changePassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">Current Password</Label>
              <div className="relative">
                <Input
                  id="currentPassword"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                >
                  {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <div className="relative">
                  <Input
                    id="newPassword"
                    type={showNewPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min 8 characters"
                    required
                    minLength={8}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  required
                  minLength={8}
                />
              </div>
            </div>

            {passwordMessage && (
              <div
                className={`text-sm flex items-center gap-2 p-3 rounded ${
                  passwordMessage.type === 'success'
                    ? 'text-green-400 bg-green-500/10 border border-green-500/20'
                    : 'text-destructive bg-destructive/10 border border-destructive/20'
                }`}
              >
                {passwordMessage.type === 'success' ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                {passwordMessage.text}
              </div>
            )}

            <div className="flex justify-end">
              <Button type="submit" disabled={passwordSaving} className="gap-2">
                <Lock className="w-4 h-4" />
                {passwordSaving ? 'Updating...' : 'Change Password'}
              </Button>
            </div>
          </form>
        </Card>

        {/* ───── API Keys Section ───── */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-violet-500/10 flex items-center justify-center">
                <Key className="w-5 h-5 text-violet-500" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">API Keys</h2>
                <p className="text-sm text-muted-foreground">Configure your LLM provider keys</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowKeyInput(!showKeyInput)}
              className="gap-2"
            >
              <Key className="w-4 h-4" />
              {showKeyInput ? 'Cancel' : 'Add Key'}
            </Button>
          </div>

          {/* Add Key Form */}
          {showKeyInput && (
            <form onSubmit={saveApiKey} className="mb-6 space-y-4 p-4 rounded-lg border border-white/10 bg-card/30">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="provider">Provider</Label>
                  <select
                    id="provider"
                    value={newKeyProvider}
                    onChange={(e) => setNewKeyProvider(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    required
                  >
                    <option value="">Select provider...</option>
                    {PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.icon} {p.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apiKey">API Key</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    value={newKeyValue}
                    onChange={(e) => setNewKeyValue(e.target.value)}
                    placeholder="sk-..."
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <Button type="submit" disabled={keySaving} className="gap-2">
                  <Save className="w-4 h-4" />
                  {keySaving ? 'Saving...' : 'Save Key'}
                </Button>
              </div>
            </form>
          )}

          {keyMessage && (
            <div
              className={`text-sm flex items-center gap-2 p-3 rounded mb-4 ${
                keyMessage.type === 'success'
                  ? 'text-green-400 bg-green-500/10 border border-green-500/20'
                  : 'text-destructive bg-destructive/10 border border-destructive/20'
              }`}
            >
              {keyMessage.type === 'success' ? (
                <Check className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              {keyMessage.text}
            </div>
          )}

          {/* Keys List */}
          {keysLoading ? (
            <div className="text-center py-6 text-muted-foreground">Loading API keys...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8">
              <Key className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">
                No API keys configured. Add your LLM provider keys to use your own accounts.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {apiKeys.map((key) => {
                const providerInfo = getProviderInfo(key.provider);
                return (
                  <div
                    key={key.provider}
                    className="flex items-center justify-between p-4 rounded-lg border border-white/10 bg-card/20"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{providerInfo.icon}</span>
                      <div>
                        <p className="font-medium">{providerInfo.label}</p>
                        <p className="text-sm text-muted-foreground font-mono">{key.masked_key}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="text-xs">
                        {new Date(key.created_at).toLocaleDateString()}
                      </Badge>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => deleteApiKey(key.provider)}
                        title="Remove API Key"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {/* Info Card */}
        <Card className="p-4 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800/30">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Security Note:</strong> API keys are encrypted at rest using Fernet encryption.
            They are never returned in full — only a masked preview is shown. If you lose access to a key,
            you'll need to re-enter it.
          </p>
        </Card>
    </PageContainer>
  );
}
