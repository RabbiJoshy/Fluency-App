// Explicit immutable login identities. Display names never grant permissions.
const ADMIN_ID = 'clerk_user_3KkMOyRxK2i4qZlXgT5VHJRmNTT'; // SafariMS
const JOSHUA_ID = 'clerk_user_3KdfOQ19QCngxtBsj0NsX3qlMjl';
const JP_ID = 'clerk_user_3KllLK7ajq5RWtvjlNdrCH2PTLk';

export function accountPermissions(identity) {
    const id = String(identity || '').replace(/^stg_/, '');
    const isAdmin = id === ADMIN_ID;
    const isJp = id === JP_ID;
    const isReviewer = id === JOSHUA_ID || isJp;
    return { role: isAdmin ? 'admin' : isReviewer ? 'reviewer' : 'learner',
        isAdmin, isReviewer, isJp, canFlag: isAdmin || isReviewer };
}
