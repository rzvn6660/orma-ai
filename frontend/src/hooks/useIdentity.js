import { useContext, createContext } from 'react';

// Create a context that holds the identity information
export const IdentityContext = createContext({
  actor: null,
  subject: null,
  permissions: [],
  role: null,
  currentPatient: null
});

export function useActor() {
  const context = useContext(IdentityContext);
  return context.actor;
}

export function useSubject() {
  const context = useContext(IdentityContext);
  return context.subject;
}

export function usePermissions() {
  const context = useContext(IdentityContext);
  return {
    permissions: context.permissions,
    can: (action) => context.permissions.includes(action),
    canRead: (resource) => context.permissions.includes(`read_${resource}`),
    canWrite: (resource) => context.permissions.includes(`write_${resource}`),
    canShare: (resource) => context.permissions.includes(`share_${resource}`),
    canDelete: (resource) => context.permissions.includes(`delete_${resource}`),
    canManage: (resource) => context.permissions.includes(`manage_${resource}`)
  };
}

export function useCurrentPatient() {
  const context = useContext(IdentityContext);
  return context.currentPatient;
}

export function useRole() {
  const context = useContext(IdentityContext);
  return context.role;
}
