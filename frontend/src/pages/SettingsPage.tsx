import { useState } from 'react';
import { useAPIClient } from '@/contexts/APIContext';
import { useFetch } from '@/hooks/useFetch';
import { useMutation } from '@/hooks/useMutation';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import {
  User,
  Lock,
  Check,
  AlertCircle,
  Eye,
  EyeOff,
  Save,
} from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';
import type { UpdateProfileInput, UpdatePasswordInput } from '@/lib/api/types';



type MessageState = { type: 'success' | 'error'; text: string } | null;

export default function SettingsPage() {
  const apiClient = useAPIClient();

  // ───── Profile Section ─────
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [profileMessage, setProfileMessage] = useState<MessageState>(null);

  const { isLoading: profileLoading } = useFetch(
    () => apiClient.settings.getProfile(),
    {
      dependencies: [apiClient],
      onSuccess: (data) => {
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setEmail(data.email);
      },
    }
  );

  const { mutate: updateProfile, isLoading: profileSaving } = useMutation(
    (data: UpdateProfileInput) => apiClient.settings.updateProfile(data),
    {
      onSuccess: () => {
        setProfileMessage({ type: 'success', text: 'Profile updated successfully' });
        setTimeout(() => setProfileMessage(null), 3000);
      },
      onError: (error) => {
        setProfileMessage({ type: 'error', text: error });
      },
    }
  );

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);
    updateProfile({
      first_name: firstName,
      last_name: lastName,
      email,
    });
  };

  // ───── Password Section ─────
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<MessageState>(null);

  const { mutate: changePassword, isLoading: passwordSaving } = useMutation(
    (data: UpdatePasswordInput) => apiClient.settings.updatePassword(data),
    {
      onSuccess: () => {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordMessage({ type: 'success', text: 'Password changed successfully' });
        setTimeout(() => setPasswordMessage(null), 3000);
      },
      onError: (error) => {
        setPasswordMessage({ type: 'error', text: error });
      },
    }
  );

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMessage({ type: 'error', text: 'Password must be at least 8 characters' });
      return;
    }

    changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    });
  };



  return (
    <PageContainer maxWidth="narrow" title="Settings" description="Manage your account settings and preferences">
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
          <form onSubmit={handleSaveProfile} className="space-y-4">
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
                {profileMessage.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
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

        <form onSubmit={handleChangePassword} className="space-y-4">
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
              {passwordMessage.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
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


      {/* Info Card */}

    </PageContainer>
  );
}
