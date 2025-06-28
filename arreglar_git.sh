#!/bin/bash

echo "=== Resolución asistida de conflictos Git ==="

# Verificar si hay conflicto de merge activo
if [ -f .git/MERGE_HEAD ]; then
  echo -e "\nConflicto de fusión detectado."

  read -p "¿Quieres abortar el merge actual? (s/n): " abort_merge
  if [[ "$abort_merge" == "s" ]]; then
    git merge --abort
    echo "Fusión abortada."
    exit 0
  fi
else
  echo "No hay fusión en conflicto actualmente."
fi

# Obtener archivos en conflicto
conflicted_files=$(git diff --name-only --diff-filter=U)

if [ -z "$conflicted_files" ]; then
  echo "No hay archivos en conflicto."
else
  echo -e "\nArchivos en conflicto detectados:"
  echo "$conflicted_files"

  for file in $conflicted_files; do
    echo -e "\n--- Resolviendo: $file ---"
    echo "Opciones:"
    echo "  1) Conservar versión LOCAL"
    echo "  2) Conservar versión REMOTA"
    echo "  3) Editar manualmente"
    read -p "Elige una opción [1-3]: " choice

    case $choice in
      1)
        git checkout --ours "$file"
        ;;
      2)
        git checkout --theirs "$file"
        ;;
      3)
        echo "Abriendo $file para edición..."
        ${EDITOR:-nano} "$file"
        ;;
      *)
        echo "Opción inválida. Saltando $file."
        continue
        ;;
    esac

    git add "$file"
    echo "Archivo $file marcado como resuelto."
  done

  # Hacer commit de resolución
  git commit -m "Conflictos de fusión resueltos automáticamente"
  echo "Commit de resolución realizado."
fi

# Confirmar cambios en staging
echo -e "\nCambios a confirmar:"
git status -s

# Traer cambios restantes desde origin/main
echo -e "\nHaciendo rebase con origin/main..."
git pull origin main --rebase

# Preguntar si se desea limpiar archivos sin seguimiento
echo -e "\nArchivos sin seguimiento:"
git clean -n

read -p "¿Deseas eliminar estos archivos sin seguimiento? (s/n): " clean_choice
if [[ "$clean_choice" == "s" ]]; then
  git clean -f
  echo "Archivos eliminados."
else
  echo "Archivos sin seguimiento conservados."
fi

echo -e "\n✅ Repositorio sincronizado y limpio."
